"""Web search fallback for the Ask AI Questions use case.

When GradApp's own records cannot answer a question, the assistant searches
the web (OpenAI's built-in ``web_search`` tool), answers with clickable source
links, and saves the graduate programs, funding opportunities and faculty it
found into GradApp so the next student gets them from the database.

Safeguards:
* Only facts stated in the cited answer are extracted; nothing is guessed.
* Every saved record must point to one of the URLs the search actually cited.
* Links must be OFFICIAL and WORKING: a program, faculty member or university
  funding record is saved only if its source page is on that university's own
  website (not an aggregator such as a rankings or study-abroad site), and
  every saved link is checked to load before it is stored.
* Saved records are marked ``origin=web`` and ``needs_review=True`` and are shown
  as "not yet reviewed" until an administrator approves them.
* Existing records are never modified by web search; only new ones are added.
"""

import ipaddress
import json
import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from programs.models import Faculty, FundingOpportunity, GraduateProgram, Origin, University

from . import llm


logger = logging.getLogger(__name__)

MAX_SAVED_PER_TYPE = 5

SEARCH_INSTRUCTIONS = """You help prospective graduate students research graduate programs.
Search the web and answer the student's question about graduate programs, admission requirements,
tuition, deadlines, funding/scholarships/assistantships, or faculty and research advisors.
Rules:
- Use and cite the OFFICIAL university or department website (the university's own domain, e.g. uh.edu)
  or the funder's own website. Do not rely on rankings, study-abroad or aggregator sites.
- Give concrete facts when available: program name, degree level, university and city, tuition per year,
  application deadline, minimum GPA, funding, and professors with their research areas.
- Cite your sources.
- You describe options; never predict admission chances.
- Keep the answer under about 200 words, using short paragraphs or bullet points.
Today's date is {today}."""

EXTRACTION_PROMPT = """Extract structured records from a web-search answer about graduate study.
Return ONLY a JSON object with this shape (use [] or null when not stated; never invent facts):
{
  "programs": [{
    "university": str, "city": str|null, "state_or_region": str|null, "country": str|null,
    "university_website": url|null,
    "name": str, "degree_level": "masters"|"doctoral"|"other", "field_of_study": str,
    "description": str|null, "tuition_per_year": number|null, "application_deadline": "YYYY-MM-DD"|null,
    "minimum_gpa": number|null, "funding_available": true|false|null, "admission_requirements": str|null,
    "source_url": url
  }],
  "funding": [{
    "name": str, "funding_type": "assistantship"|"fellowship"|"scholarship"|"grant"|"other",
    "university": str|null, "provider": str|null, "amount": number|null, "amount_note": str|null,
    "eligibility": str|null, "international_eligible": true|false|null, "deadline": "YYYY-MM-DD"|null,
    "description": str|null, "source_url": url
  }],
  "faculty": [{
    "name": str, "title": str|null, "department": str|null, "university": str,
    "research_areas": [str], "source_url": url
  }]
}
Rules:
- Include only records the answer text explicitly describes. A program needs a university and program name.
- "source_url" MUST be copied exactly from the numbered source list provided, and must be a page on the
  university's (or funder's) OWN website. Skip a record if only third-party sites support it.
- "university_website" is the university's official home page (e.g. https://www.uh.edu/), or null.
- Numbers are digits only (no $ or commas). Dates must be explicit in the text; otherwise null."""

_MD_LINK_PAREN_RE = re.compile(r"\s*\(\[([^\]]+)\]\((https?://[^)\s]+)\)\)")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def _replace_links_with_refs(text, citations):
    """Turn inline markdown links into [W1]-style references matching ``citations``."""
    index = {citation["url"]: position for position, citation in enumerate(citations, start=1)}

    def ref_for(url):
        url = llm.clean_url(url)
        if url not in index:
            citations.append({"url": url, "title": url})
            index[url] = len(citations)
        return f"[W{index[url]}]"

    text = _MD_LINK_PAREN_RE.sub(lambda m: " " + ref_for(m.group(2)), text)
    text = _MD_LINK_RE.sub(lambda m: f"{m.group(1)} {ref_for(m.group(2))}", text)
    return text.strip()


def _parse_json(reply):
    if not reply:
        return {}
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _text(value, limit=255):
    return str(value).strip()[:limit] if value not in (None, "") else ""


def _decimal(value, maximum=None):
    if value in (None, ""):
        return None
    try:
        number = Decimal(str(value).replace(",", "").replace("$", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0 or (maximum is not None and number > maximum):
        return None
    return number


def _date(value):
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def _site_root(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else ""


# --------------------------------------------------------------------------
# Official, working links
# --------------------------------------------------------------------------

# Rankings, study-abroad, social and other third-party sites are never saved as official links.
AGGREGATOR_DOMAINS = {
    "collegedunia.com", "yocket.com", "shiksha.com", "leverageedu.com", "gyandhan.com", "uni4edu.com",
    "studee.com", "studyportals.com", "mastersportal.com", "phdportal.com", "petersons.com", "usnews.com",
    "niche.com", "gradschools.com", "topuniversities.com", "timeshighereducation.com", "collegevine.com",
    "collegeboard.org", "unigo.com", "scholars4dev.com", "scholarshipsads.com", "opportunitydesk.org",
    "globalscholarships.com", "scholarshipscentral.com", "applysquare.com", "idp.com", "edvoy.com",
    "gradright.com", "upgrad.com", "canamgroup.com", "kaplaninternational.com", "wikipedia.org",
    "linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com", "reddit.com",
    "quora.com", "medium.com", "glassdoor.com", "indeed.com", "ratemyprofessors.com", "researchgate.net",
    "google.com", "googleusercontent.com", "github.io", "blogspot.com", "wordpress.com",
}
_SECOND_LEVEL = {"ac", "edu", "co", "gov", "org", "com", "net"}


def registrable_domain(url):
    """``https://www.cs.uh.edu/x`` -> ``uh.edu``; ``https://www.ox.ac.uk`` -> ``ox.ac.uk``."""
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    if not host:
        return ""
    try:
        ipaddress.ip_address(host)
        return ""  # raw IP addresses are never official links
    except ValueError:
        pass
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in _SECOND_LEVEL and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def is_aggregator(url):
    domain = registrable_domain(url)
    host = (urlparse(url).hostname or "").lower()
    return not domain or domain in AGGREGATOR_DOMAINS or any(host.endswith("." + d) for d in AGGREGATOR_DOMAINS)


def link_is_live(url):
    """True if the page loads (follows redirects). Bot-blocking responses count as live."""
    if not settings.AI_REQUIRE_LIVE_LINKS:
        return True
    from programs.retrieval import RetrievalBlocked, validate_public_url

    try:
        validate_public_url(url)
        headers = {"User-Agent": settings.RETRIEVAL_USER_AGENT}
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
        if response.status_code in (405, 501):  # HEAD not allowed: try GET
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=8, stream=True)
            response.close()
    except (RetrievalBlocked, requests.RequestException, ValueError):
        return False
    return response.status_code < 400 or response.status_code in (401, 403, 429)


def official_university_website(item, source):
    """The university's official home page on the same domain as ``source``."""
    domain = registrable_domain(source)
    candidate = str(item.get("university_website") or "")
    if candidate.startswith(("http://", "https://")) and registrable_domain(candidate) == domain and link_is_live(candidate):
        return candidate
    for guess in (f"https://www.{domain}/", f"https://{domain}/"):
        if link_is_live(guess):
            return guess
    return _site_root(source)


def is_academic_domain(domain):
    """uh.edu, ox.ac.uk, unimelb.edu.au ... (other countries' universities are checked via their website)."""
    return domain.endswith(".edu") or ".edu." in domain or ".ac." in domain


def official_source(item, allowed_urls, university=None, institutional=True):
    """Return the record's cited source if it is an official, working page, else ``None``.

    * Institutional records (programs, faculty, a university's own funding) must come from
      the university's own domain. If the university is already in GradApp, its stored
      website decides the domain; otherwise the source must be an academic domain (.edu,
      .ac.xx) or match the official website the answer gave for the university.
    * External funding (e.g. a national fellowship) must come from the funder's site,
      which may not be a rankings/aggregator/social site.
    """
    source = llm.clean_url(item.get("source_url") or "")
    if source not in allowed_urls or is_aggregator(source):
        return None
    domain = registrable_domain(source)
    if institutional:
        if university is not None:
            if domain != registrable_domain(university.website_url):
                return None
        else:
            website = str(item.get("university_website") or "")
            if not (is_academic_domain(domain) or (website and registrable_domain(website) == domain)):
                return None
    if not link_is_live(source):
        return None
    return source


def _get_or_create_university(data, source_url):
    name = _text(data.get("university"))
    if not name:
        return None
    university = University.objects.filter(name__iexact=name).first()
    if university:
        return university
    website = official_university_website(data, source_url)
    return University.objects.create(
        name=name,
        city=_text(data.get("city"), 120) or "Unknown",
        state_or_region=_text(data.get("state_or_region"), 120),
        country=_text(data.get("country"), 120) or "Unknown",
        website_url=website,
    )


def _save_records(data, allowed_urls):
    """Create new, review-flagged records. Returns a list of source dicts."""
    saved = []
    now = timezone.now()

    for item in (data.get("programs") or [])[:MAX_SAVED_PER_TYPE]:
        name = _text(item.get("name"))
        existing = University.objects.filter(name__iexact=_text(item.get("university"))).first()
        source = official_source(item, allowed_urls, existing)
        if not source or not name or not item.get("university"):
            continue
        university = _get_or_create_university(item, source)
        if not university:
            continue
        degree = item.get("degree_level") if item.get("degree_level") in {"masters", "doctoral", "other"} else "other"
        program = GraduateProgram.objects.filter(university=university, name__iexact=name, degree_level=degree).first()
        created = program is None
        if created:
            program = GraduateProgram.objects.create(
                university=university,
                name=name,
                degree_level=degree,
                field_of_study=_text(item.get("field_of_study"), 180) or name,
                description=_text(item.get("description"), 2000),
                admission_requirements=_text(item.get("admission_requirements"), 2000),
                tuition_per_year=_decimal(item.get("tuition_per_year")),
                minimum_gpa=_decimal(item.get("minimum_gpa"), maximum=4),
                funding_available=bool(item.get("funding_available")),
                application_deadline=_date(item.get("application_deadline")),
                program_url=source,
                source_retrieved_at=now,
                origin=Origin.WEB,
                needs_review=True,
            )
        saved.append({"type": "program", "ref": f"P{program.id}", "id": program.id,
                      "title": f"{program.name} - {university.name}", "url": program.program_url,
                      "saved": True, "created": created})

    for item in (data.get("funding") or [])[:MAX_SAVED_PER_TYPE]:
        name = _text(item.get("name"))
        has_university = bool(item.get("university"))
        existing = University.objects.filter(name__iexact=_text(item.get("university"))).first() if has_university else None
        source = official_source(item, allowed_urls, existing, institutional=has_university)
        if not source or not name:
            continue
        university = _get_or_create_university(item, source) if item.get("university") else None
        funding = FundingOpportunity.objects.filter(name__iexact=name, university=university).first()
        created = funding is None
        if created:
            funding_type = item.get("funding_type")
            if funding_type not in {"assistantship", "fellowship", "scholarship", "grant", "other"}:
                funding_type = "other"
            international = item.get("international_eligible")
            funding = FundingOpportunity.objects.create(
                name=name,
                funding_type=funding_type,
                university=university,
                provider=_text(item.get("provider")) or (university.name if university else ""),
                description=_text(item.get("description"), 2000),
                eligibility=_text(item.get("eligibility"), 2000),
                amount=_decimal(item.get("amount")),
                amount_note=_text(item.get("amount_note")),
                international_eligible=True if international is None else bool(international),
                deadline=_date(item.get("deadline")),
                url=source,
                origin=Origin.WEB,
                needs_review=True,
            )
        saved.append({"type": "funding", "ref": f"G{funding.id}", "id": funding.id, "title": funding.name,
                      "url": funding.url, "saved": True, "created": created})

    for item in (data.get("faculty") or [])[:MAX_SAVED_PER_TYPE]:
        name = _text(item.get("name"), 180)
        existing = University.objects.filter(name__iexact=_text(item.get("university"))).first()
        source = official_source(item, allowed_urls, existing)
        if not source or not name or not item.get("university"):
            continue
        university = _get_or_create_university(item, source)
        if not university:
            continue
        member = Faculty.objects.filter(name__iexact=name, university=university).first()
        created = member is None
        if created:
            areas = item.get("research_areas") or []
            if isinstance(areas, str):
                areas = [areas]
            member = Faculty.objects.create(
                university=university,
                name=name,
                title=_text(item.get("title"), 180),
                department=_text(item.get("department"), 180),
                research_areas=", ".join(_text(area, 80) for area in areas if area)[:1000],
                profile_url=source,
                origin=Origin.WEB,
                needs_review=True,
            )
        saved.append({"type": "faculty", "ref": f"F{member.id}", "id": member.id,
                      "title": f"{member.name} - {university.name}", "url": member.profile_url,
                      "saved": True, "created": created})
    return saved


def search_web_and_save(question):
    """Answer ``question`` from the web and save what was found.

    Returns ``{"answer", "sources", "saved"}`` or ``None`` if web search is unavailable.
    """
    result = llm.web_search(SEARCH_INSTRUCTIONS.format(today=date.today().isoformat()), question)
    if not result:
        return None
    citations = list(result["citations"])
    answer = _replace_links_with_refs(result["text"], citations)

    saved = []
    if citations:
        source_list = "\n".join(f"{i}. {c['title']} - {c['url']}" for i, c in enumerate(citations, start=1))
        reply = llm.complete(
            EXTRACTION_PROMPT,
            [{"role": "user", "content": f"Question: {question}\n\nAnswer:\n{answer}\n\nSources:\n{source_list}"}],
            max_tokens=1800,
        )
        try:
            with transaction.atomic():
                saved = _save_records(_parse_json(reply), {c["url"] for c in citations})
        except Exception as exc:  # never fail the answer because saving failed
            logger.warning("Could not save web search results: %s", exc)
            saved = []

    web_sources = [
        {"type": "web", "ref": f"W{i}", "title": c["title"], "url": c["url"]}
        for i, c in enumerate(citations, start=1)
    ]
    return {"answer": answer, "sources": web_sources + saved, "saved": saved}
