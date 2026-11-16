from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gradapp.testutils import make_program, make_university, make_user
from programs.models import FundingOpportunity, GraduateProgram, University

from .models import ChatMessage, Conversation


WEB_TEXT = (
    "The University of Houston offers an MS in Computer Science ([uh.edu](https://www.uh.edu/cs/ms?utm_source=openai)). "
    "Tuition is about $14,000 per year. The Cullen Fellowship provides $5,000 "
    "([uh.edu](https://www.uh.edu/funding))."
)
CITATIONS = [
    {"url": "https://www.uh.edu/cs/ms", "title": "MS in Computer Science - University of Houston"},
    {"url": "https://www.uh.edu/funding", "title": "Graduate funding - University of Houston"},
]
EXTRACTED = """{
  "programs": [
    {"university": "University of Houston", "city": "Houston", "state_or_region": "Texas", "country": "United States",
     "name": "Computer Science", "degree_level": "masters", "field_of_study": "Computer Science",
     "tuition_per_year": 14000, "source_url": "https://www.uh.edu/cs/ms"},
    {"university": "Invented University", "name": "Fake Program", "degree_level": "masters",
     "field_of_study": "Fake", "source_url": "https://not-a-cited-source.example/"}
  ],
  "funding": [
    {"name": "Cullen Fellowship", "funding_type": "fellowship", "university": "University of Houston",
     "amount": 5000, "source_url": "https://www.uh.edu/funding"}
  ],
  "faculty": []
}"""


def web_result():
    return {"text": WEB_TEXT, "citations": [dict(c) for c in CITATIONS]}


@mock.patch("assistant.web.link_is_live", return_value=True)
@mock.patch("assistant.qa.llm.is_configured", return_value=True)
class WebSearchFallbackTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(make_user())

    def ask(self, question, **extra):
        return self.client.post(reverse("ai-ask"), {"question": question, "use_profile": False, **extra}, format="json")

    @mock.patch("assistant.web.llm.complete", return_value=EXTRACTED)
    @mock.patch("assistant.web.llm.web_search", side_effect=lambda *a, **k: web_result())
    def test_no_records_triggers_web_search_and_saves_results(self, web_search, _complete, _configured, _live):
        response = self.ask("Tell me about the MS in Computer Science at the University of Houston")
        self.assertTrue(response.data["web_searched"])
        web_search.assert_called_once()

        # Inline markdown links become clickable [W1] references, without tracking parameters.
        self.assertIn("[W1]", response.data["answer"])
        self.assertNotIn("utm_source", response.data["answer"])
        refs = [source["ref"] for source in response.data["sources"]]
        self.assertEqual(refs[:2], ["W1", "W2"])

        program = GraduateProgram.objects.get(name="Computer Science", university__name="University of Houston")
        self.assertTrue(program.needs_review)
        self.assertEqual(program.origin, "web")
        self.assertEqual(str(program.tuition_per_year), "14000.00")
        self.assertEqual(program.program_url, "https://www.uh.edu/cs/ms")
        funding = FundingOpportunity.objects.get(name="Cullen Fellowship")
        self.assertTrue(funding.needs_review)
        self.assertEqual(funding.funding_type, "fellowship")
        # A record whose source was not actually cited is never saved.
        self.assertFalse(University.objects.filter(name="Invented University").exists())
        saved_refs = [s["ref"] for s in response.data["saved"]]
        self.assertEqual(saved_refs, [f"P{program.id}", f"G{funding.id}"])

    @mock.patch("assistant.web.llm.complete", return_value=EXTRACTED)
    @mock.patch("assistant.web.llm.web_search", side_effect=lambda *a, **k: web_result())
    def test_saved_records_answer_the_next_question_from_gradapp(self, _web_search, _complete, _configured, _live):
        self.ask("Tell me about the MS in Computer Science at the University of Houston")
        with mock.patch("assistant.qa.llm.complete", return_value="See [P1].") as answer:
            response = self.ask("What is the tuition for computer science in Houston?")
        self.assertFalse(response.data["web_searched"])
        self.assertIn("University of Houston", answer.call_args.args[1][-1]["content"])

    @mock.patch("assistant.web.llm.complete", return_value=EXTRACTED)
    @mock.patch("assistant.web.llm.web_search", side_effect=lambda *a, **k: web_result())
    def test_existing_records_are_never_modified(self, _web_search, _complete, _configured, _live):
        houston = make_university("University of Houston", city="Houston")
        existing = make_program(houston, "Computer Science", tuition_per_year=99999)
        self.ask("anything", search_web=True)
        existing.refresh_from_db()
        self.assertEqual(str(existing.tuition_per_year), "99999.00")
        self.assertFalse(existing.needs_review)
        self.assertEqual(GraduateProgram.objects.filter(university=houston).count(), 1)

    @mock.patch("assistant.web.llm.complete", return_value="{}")
    @mock.patch("assistant.web.llm.web_search", side_effect=lambda *a, **k: web_result())
    def test_records_that_cannot_answer_trigger_web_search(self, web_search, _complete, _configured, _live):
        make_program(make_university(), "Data Science", description="Statistics.")
        with mock.patch("assistant.qa.llm.complete", return_value="NO_ANSWER"):
            response = self.ask("Which data science programs are in Houston?")
        self.assertTrue(response.data["web_searched"])
        web_search.assert_called_once()

    @mock.patch("assistant.web.llm.web_search")
    def test_search_web_button_skips_database(self, web_search, _configured, _live):
        web_search.return_value = {"text": "From the web.", "citations": []}
        make_program(make_university(), "Data Science")
        with mock.patch("assistant.qa.llm.complete") as answer_from_records:
            response = self.ask("Data Science", search_web=True)
        answer_from_records.assert_not_called()
        self.assertEqual(response.data["answer"], "From the web.")

    @mock.patch("assistant.web.llm.web_search", return_value=None)
    def test_failed_web_search_falls_back_gracefully(self, _web_search, _configured, _live):
        with mock.patch("assistant.qa.llm.complete", return_value=None):
            response = self.ask("zzzz qqqq")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["web_searched"])
        self.assertIn("couldn't find", response.data["answer"])

    def test_web_search_disabled_setting(self, _configured, _live):
        with self.settings(AI_WEB_SEARCH_ENABLED=False), \
             mock.patch("assistant.web.llm.web_search") as web_search, \
             mock.patch("assistant.qa.llm.complete", return_value=None):
            self.ask("zzzz qqqq")
        web_search.assert_not_called()


class WebSearchClientTests(APITestCase):
    def test_parses_citations_and_strips_tracking(self):
        from . import llm

        annotation = mock.Mock(type="url_citation", url="https://www.uh.edu/cs?utm_source=openai", title="UH CS")
        part = mock.Mock(annotations=[annotation, annotation])
        message = mock.Mock(type="message", content=[part])
        response = mock.Mock(output=[mock.Mock(type="web_search_call"), message], output_text=" Answer. ")
        client = mock.Mock()
        client.responses.create.return_value = response
        with self.settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="gpt-test"), \
             mock.patch.object(llm, "_get_client", return_value=client):
            result = llm.web_search("instructions", "question")
        self.assertEqual(result, {"text": "Answer.", "citations": [{"url": "https://www.uh.edu/cs", "title": "UH CS"}]})
        kwargs = client.responses.create.call_args.kwargs
        self.assertEqual(kwargs["tools"], [{"type": "web_search"}])
        self.assertEqual(kwargs["model"], "gpt-test")


class ConversationTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(self.user)
        make_program(make_university(), "Data Science", description="Machine learning.")

    def test_create_send_and_continue_conversation(self):
        conversation = self.client.post(reverse("conversation-list"), {}, format="json").data
        url = reverse("conversation-messages", args=[conversation["id"]])

        first = self.client.post(url, {"question": "Which programs teach machine learning?"}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual([m["role"] for m in first.data["messages"]], ["user", "assistant"])
        self.assertEqual(first.data["conversation"]["title"], "Which programs teach machine learning?")

        with mock.patch("assistant.views.answer_question", return_value={
            "answer": "Follow-up answer.", "sources": [], "ai_powered": True, "web_searched": False, "saved": [],
        }) as answer:
            self.client.post(url, {"question": "What about funding?"}, format="json")
        history = answer.call_args.kwargs["history"]
        self.assertEqual(history[0], {"role": "user", "content": "Which programs teach machine learning?"})
        self.assertEqual(history[-1]["role"], "assistant")

        detail = self.client.get(reverse("conversation-detail", args=[conversation["id"]])).data
        self.assertEqual(len(detail["messages"]), 4)
        self.assertEqual(detail["messages"][-1]["content"], "Follow-up answer.")
        listing = self.client.get(reverse("conversation-list")).data
        self.assertEqual(listing["results"][0]["message_count"], 4)

    def test_rename_and_delete(self):
        conversation = Conversation.objects.create(user=self.user)
        ChatMessage.objects.create(conversation=conversation, role="user", content="hi")
        url = reverse("conversation-detail", args=[conversation.id])
        self.assertEqual(self.client.patch(url, {"title": "My CS search"}, format="json").data["title"], "My CS search")
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatMessage.objects.exists())

    def test_conversations_are_private(self):
        other = Conversation.objects.create(user=make_user("other"))
        self.assertEqual(self.client.get(reverse("conversation-detail", args=[other.id])).status_code, 404)
        response = self.client.post(reverse("conversation-messages", args=[other.id]), {"question": "hi"}, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get(reverse("conversation-list")).data["count"], 0)


class OfficialLinkRulesTests(APITestCase):
    """Ask AI only saves records whose links are official and working."""

    def save(self, data, citations, live=True):
        from .web import _save_records

        with mock.patch("assistant.web.link_is_live", return_value=live):
            return _save_records(data, set(citations))

    def program(self, **extra):
        item = {"university": "University of Houston", "city": "Houston", "country": "United States",
                "name": "Computer Science", "degree_level": "masters", "field_of_study": "Computer Science",
                "source_url": "https://www.uh.edu/nsm/computer-science/graduate/"}
        item.update(extra)
        return {"programs": [item]}

    def test_official_university_page_is_saved(self):
        saved = self.save(self.program(), ["https://www.uh.edu/nsm/computer-science/graduate/"])
        self.assertEqual(len(saved), 1)
        program = GraduateProgram.objects.get(pk=saved[0]["id"])
        self.assertEqual(program.program_url, "https://www.uh.edu/nsm/computer-science/graduate/")
        self.assertTrue(program.university.website_url.startswith("https://www.uh.edu"))

    def test_aggregator_sources_are_never_saved(self):
        url = "https://collegedunia.com/usa/university/1429-university-of-houston/ms-cs"
        self.assertEqual(self.save(self.program(source_url=url), [url]), [])
        self.assertFalse(GraduateProgram.objects.exists())

    def test_non_university_site_rejected_for_new_university(self):
        url = "https://www.some-education-blog.com/uh-ms-cs"
        self.assertEqual(self.save(self.program(source_url=url), [url]), [])

    def test_non_us_university_accepted_when_domain_matches_its_website(self):
        url = "https://www.utoronto.ca/academics/computer-science-msc"
        data = self.program(university="University of Toronto", source_url=url, university_website="https://www.utoronto.ca/")
        self.assertEqual(len(self.save(data, [url])), 1)

    def test_source_must_match_existing_university_domain(self):
        University.objects.create(name="University of Houston", city="Houston", state_or_region="Texas",
                                  website_url="https://www.uh.edu/")
        url = "https://www.utdallas.edu/some-page"
        self.assertEqual(self.save(self.program(source_url=url), [url]), [])

    def test_dead_links_are_not_saved(self):
        url = "https://www.uh.edu/nsm/computer-science/graduate/"
        self.assertEqual(self.save(self.program(), [url], live=False), [])

    def test_external_funding_from_funder_site_is_saved(self):
        url = "https://www.nsf.gov/funding/grfp"
        data = {"funding": [{"name": "NSF GRFP", "funding_type": "fellowship", "source_url": url}]}
        saved = self.save(data, [url])
        self.assertEqual(FundingOpportunity.objects.get(pk=saved[0]["id"]).url, url)

    def test_registrable_domain(self):
        from .web import is_aggregator, registrable_domain

        self.assertEqual(registrable_domain("https://www2.cs.uh.edu/~x"), "uh.edu")
        self.assertEqual(registrable_domain("https://www.ox.ac.uk/admissions"), "ox.ac.uk")
        self.assertEqual(registrable_domain("http://127.0.0.1/x"), "")
        self.assertTrue(is_aggregator("https://www.yocket.com/x"))
        self.assertTrue(is_aggregator("https://someone.github.io/"))
        self.assertFalse(is_aggregator("https://www.cs.utexas.edu/graduate/apply"))

    def test_link_check_treats_bot_blocking_as_live_and_404_as_dead(self):
        from .web import link_is_live

        with mock.patch("programs.retrieval.validate_public_url"), mock.patch("assistant.web.requests.head") as head:
            head.return_value = mock.Mock(status_code=403)
            self.assertTrue(link_is_live("https://www.uh.edu/"))
            head.return_value = mock.Mock(status_code=404)
            self.assertFalse(link_is_live("https://www.uh.edu/missing"))
            head.side_effect = __import__("requests").ConnectionError()
            self.assertFalse(link_is_live("https://www.uh.edu/"))
