"""Load GradApp's starter data: REAL graduate programs, faculty and funding.

Every record below was copied from the official page in its URL field and
checked on ``VERIFIED_ON``. Facts the official pages did not state (often
tuition) are left empty rather than estimated, and no record uses a placeholder
web address.

Running the command also removes the fictional sample records that earlier
versions of GradApp created (universities ending in "(Sample)").

Deadlines and requirements change every year: the "last verified" badge turns
into a warning after 90 days. Refresh records with ``retrieve_programs``, the
data admin, or by asking the AI assistant (which saves new official pages).
"""

from datetime import date, datetime, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from programs.models import Faculty, FundingOpportunity, GraduateProgram, University


VERIFIED_ON = date(2026, 11, 16)

UNIVERSITIES = [
    {"key": "tamucc", "name": "Texas A&M University-Corpus Christi", "city": "Corpus Christi", "state_or_region": "Texas", "country": "United States", "website_url": "https://www.tamucc.edu/"},
    {"key": "uh", "name": "University of Houston", "city": "Houston", "state_or_region": "Texas", "country": "United States", "website_url": "https://www.uh.edu/"},
    {"key": "utd", "name": "The University of Texas at Dallas", "city": "Richardson", "state_or_region": "Texas", "country": "United States", "website_url": "https://www.utdallas.edu/"},
    {"key": "ut", "name": "The University of Texas at Austin", "city": "Austin", "state_or_region": "Texas", "country": "United States", "website_url": "https://www.utexas.edu/"},
]

UH_CS_ADMISSIONS = "https://www.uh.edu/nsm/computer-science/graduate/admissions/"
UTD_CS_CATALOG = "https://catalog.utdallas.edu/2026/graduate/programs/ecs/computer-science"
UTD_SE_CATALOG = "https://catalog.utdallas.edu/2026/graduate/programs/ecs/software-engineering"
UT_CS_APPLY = "https://www.cs.utexas.edu/graduate/apply"

UH_CS_DEADLINES = (
    "Deadlines: fall - January 15 (international) and June 1 (U.S. citizens/permanent residents); "
    "spring - October 1 (all applicants). "
)
UT_CS_REQUIREMENTS = (
    "Application opens October 15; deadline December 15; recommendation letters due December 20. "
    "Bachelor's degree with a GPA of at least 3.0 on a 4.0 scale in upper-division and graduate coursework. "
    "At least three letters of recommendation and a statement of purpose. GRE optional (not submitting it "
    "does not count against you). Apply through the UT Austin Graduate School application and MyStatus. "
)
UTD_MS_REQUIREMENTS = (
    "Deadlines: fall - May 1, spring - October 1, summer - March 1. A bachelor's degree with two semesters "
    "of calculus, one of linear algebra and a strong programming foundation. GPA of at least 3.0 in the last "
    "60 semester credit hours and at least 3.3 in quantitative courses. GRE optional (if submitted, 308 "
    "combined with 153 verbal, 155 quantitative and 4 analytical writing is advisable). One letter of "
    "recommendation and a statement of purpose. TOEFL iBT 80 for international applicants."
)

# key, university, fields...
PROGRAMS = [
    {
        "key": "tamucc-ms-cs",
        "university": "tamucc",
        "name": "Computer Science",
        "degree_level": "masters",
        "field_of_study": "Computer Science",
        "department": "Computer Science Program, College of Engineering and Computer Science",
        "description": (
            "MS in Computer Science with a thesis option (minimum 30 credit hours) and a course-only option "
            "(minimum 36 credit hours). Core courses: Design and Analysis of Algorithms, Advanced Computer "
            "Architecture and Advanced Operating Systems. Course-only students take electives across three "
            "tracks: Software and Programming, Data Science, and Cyber Science."
        ),
        "admission_requirements": (
            "Application and fee; transcripts; a 500-1,000 word essay on why you want a master's degree and your "
            "areas of interest; GRE scores taken within five years; TOEFL or IELTS for international students. "
            "Prerequisites: data structures, a high-level programming language, computer architecture, operating "
            "systems, software engineering, discrete mathematics, calculus and one junior-level math course; "
            "missing prerequisites can be completed as leveling courses (grade B or better). "
            "The catalog lists no minimum GPA or application deadline; check the Graduate Admissions office."
        ),
        "minimum_gpa": None,
        "application_deadline": None,
        "program_url": "https://catalog.tamucc.edu/graduate/engineering/masters/computer-science-ms/",
    },
    {
        "key": "uh-ms-cs",
        "university": "uh",
        "name": "Computer Science",
        "degree_level": "masters",
        "field_of_study": "Computer Science",
        "department": "Department of Computer Science, College of Natural Sciences and Mathematics",
        "description": (
            "MS in Computer Science with five tracks: Core, Data Analytics, Parallel and Distributed Systems, "
            "Interactive Media, and Artificial Intelligence. A thesis option is available for students who "
            "identify faculty they want to work with."
        ),
        "admission_requirements": UH_CS_DEADLINES + (
            "The AI track does not admit in spring. Three recommendation letters, statement of purpose, "
            "resume/CV and transcripts. GRE required for the Core, Data Analytics, Parallel and Distributed "
            "Systems and Interactive Media tracks; optional for the AI track. English proficiency: TOEFL iBT 79, "
            "IELTS 6.5 or Duolingo 105. No minimum GPA is stated; competitive applicants typically have 3.0/4.0 "
            "or higher. Application fee: waived for U.S. citizens and permanent residents, $80 for international "
            "applicants."
        ),
        "minimum_gpa": None,
        "application_deadline": date(2027, 1, 15),
        "program_url": UH_CS_ADMISSIONS,
    },
    {
        "key": "uh-phd-cs",
        "university": "uh",
        "name": "Computer Science",
        "degree_level": "doctoral",
        "field_of_study": "Computer Science",
        "department": "Department of Computer Science, College of Natural Sciences and Mathematics",
        "description": (
            "PhD in Computer Science. Department research spans artificial intelligence, data analytics, "
            "computer systems, theory, cybersecurity and human-computer interaction."
        ),
        "admission_requirements": UH_CS_DEADLINES + (
            "Three recommendation letters, statement of purpose, resume/CV and transcripts. English proficiency: "
            "TOEFL iBT 79, IELTS 6.5 or Duolingo 105. Application fee: waived for U.S. citizens and permanent "
            "residents, $80 for international applicants."
        ),
        "minimum_gpa": None,
        "application_deadline": date(2027, 1, 15),
        "program_url": UH_CS_ADMISSIONS,
    },
    {
        "key": "uh-ms-sds",
        "university": "uh",
        "name": "Statistics and Data Science",
        "degree_level": "masters",
        "field_of_study": "Data Science",
        "department": "Department of Mathematics",
        "description": (
            "MS in Statistics & Data Science (fall admission only). A math major is not required; probability, "
            "statistics and programming experience help but are not required. Tuition follows the UH tuition "
            "calculator plus a $200-per-credit-hour MSDS course fee."
        ),
        "admission_requirements": (
            "Deadlines (fall only): April 1, 5 p.m. Central (international) and June 1, 5 p.m. Central (U.S. "
            "citizens). Bachelor's or master's degree with Calculus II and Linear Algebra or equivalent. "
            "Cumulative GPA of at least 3.00 in the last 60 hours. GRE waived. Three letters of recommendation "
            "(at least one from a faculty member), resume, personal statement, and English test scores when "
            "applicable. A Fast Track option is available to current UH undergraduates and recent alumni."
        ),
        "minimum_gpa": "3.00",
        "application_deadline": date(2027, 4, 1),
        "program_url": "https://www.uh.edu/nsm/math/graduate/ms-statistics-data-science/admission-application/",
    },
    {
        "key": "utd-ms-cs",
        "university": "utd",
        "name": "Computer Science",
        "degree_level": "masters",
        "field_of_study": "Computer Science",
        "department": "Erik Jonsson School of Engineering and Computer Science",
        "description": (
            "MS in Computer Science (minimum 33 semester credit hours; the thesis plan is 27 course hours plus "
            "6 thesis hours). Tracks: Data Sciences, Cyber Security, Intelligent Systems, Interactive Computing, "
            "Networks and Telecommunications, Systems, and Traditional Computer Science."
        ),
        "admission_requirements": UTD_MS_REQUIREMENTS,
        "minimum_gpa": "3.00",
        "application_deadline": date(2027, 3, 1),
        "program_url": UTD_CS_CATALOG,
    },
    {
        "key": "utd-ms-se",
        "university": "utd",
        "name": "Software Engineering",
        "degree_level": "masters",
        "field_of_study": "Software Engineering",
        "department": "Erik Jonsson School of Engineering and Computer Science",
        "description": "MS in Software Engineering (minimum 33 semester credit hours). Admission is competitive.",
        "admission_requirements": UTD_MS_REQUIREMENTS.replace(" TOEFL iBT 80 for international applicants.", ""),
        "minimum_gpa": "3.00",
        "application_deadline": date(2027, 3, 1),
        "program_url": UTD_SE_CATALOG,
    },
    {
        "key": "utd-phd-se",
        "university": "utd",
        "name": "Software Engineering",
        "degree_level": "doctoral",
        "field_of_study": "Software Engineering",
        "department": "Erik Jonsson School of Engineering and Computer Science",
        "description": (
            "PhD in Software Engineering (minimum 75 semester credit hours beyond the bachelor's degree), with a "
            "qualifying examination and a dissertation."
        ),
        "admission_requirements": (
            "Deadlines: fall - December 15, spring - May 15, summer - October 15. Either a master's degree in "
            "computer science or equivalent with a GPA of at least 3.5, or a related bachelor's degree with two "
            "semesters of calculus and linear algebra and a GPA of at least 3.5 in the last 60 semester credit "
            "hours. GRE optional but advisable. Three letters of recommendation, a statement of purpose and a resume."
        ),
        "minimum_gpa": "3.50",
        "application_deadline": date(2026, 12, 15),
        "program_url": UTD_SE_CATALOG,
    },
    {
        "key": "ut-ms-cs",
        "university": "ut",
        "name": "Computer Science",
        "degree_level": "masters",
        "field_of_study": "Computer Science",
        "department": "Department of Computer Science",
        "description": (
            "On-campus MS in Computer Science (30 credit hours) with thesis and non-thesis options. A STEM-designated "
            "degree; the department also offers an online MSCS through its Computer & Data Science Online program."
        ),
        "admission_requirements": UT_CS_REQUIREMENTS + "Master's admission decisions are released April 1.",
        "minimum_gpa": "3.00",
        "application_deadline": date(2026, 12, 15),
        "program_url": UT_CS_APPLY,
    },
    {
        "key": "ut-phd-cs",
        "university": "ut",
        "name": "Computer Science",
        "degree_level": "doctoral",
        "field_of_study": "Computer Science",
        "department": "Department of Computer Science",
        "description": "PhD in Computer Science at UT Austin's Department of Computer Science.",
        "admission_requirements": UT_CS_REQUIREMENTS + "PhD admission decisions are released March 30.",
        "minimum_gpa": "3.00",
        "application_deadline": date(2026, 12, 15),
        "program_url": UT_CS_APPLY,
    },
]

UH_ALGORITHMS = "Listed in the University of Houston Computer Science Algorithms research area."
UTD_ML_PAGE = "https://machine-learning.utdallas.edu/who-we-are"
UTD_ML_NOTE = "Title and interests as listed by the UT Dallas Center for Machine Learning."
UT_ML_NOTE = "Listed in UT Austin Computer Science Machine Learning research."
UT_PROFILE = "https://www.cs.utexas.edu/people/faculty-researchers/"

# university, name, title, research areas, profile URL, program keys, bio
FACULTY = [
    ("uh", "Stephen Huang", "Professor of Computer Science", "cybersecurity, intrusion detection, cyber behavior analytics, algorithms",
     "https://www.uh.edu/nsm/computer-science/people/faculty/profiles/stephenhuang.php", ["uh-ms-cs", "uh-phd-cs"], UH_ALGORITHMS),
    ("uh", "Rathish Das", "Assistant Professor", "approximation algorithms, parallel algorithms",
     "https://www.uh.edu/nsm/computer-science/people/faculty/profiles/rathishdas.php", ["uh-ms-cs", "uh-phd-cs"], UH_ALGORITHMS),
    ("uh", "Gopal Pandurangan", "", "algorithms, distributed computing",
     "https://www.uh.edu/nsm/computer-science/people/faculty/profiles/gopalpandurangan.php", ["uh-ms-cs", "uh-phd-cs"], UH_ALGORITHMS),
    ("uh", "Rakesh Verma", "", "cybersecurity, reasoning and data analytics for security",
     "https://www2.cs.uh.edu/~rmverma/", ["uh-ms-cs", "uh-phd-cs"], UH_ALGORITHMS),
    ("uh", "Carlos Ordonez", "", "big data systems, artificial intelligence",
     "https://www2.cs.uh.edu/~ordonez/", ["uh-ms-cs", "uh-phd-cs"], UH_ALGORITHMS),
    ("uh", "Panruo Wu", "Associate Professor", "algorithms, parallel computing",
     "https://www2.cs.uh.edu/~panruowu/", ["uh-ms-cs", "uh-phd-cs"], UH_ALGORITHMS),
    ("utd", "Sriraam Natarajan", "Professor; Director, Center for Machine Learning",
     "artificial intelligence, machine learning, statistical relational learning, reinforcement learning, graphical models, biomedical applications",
     UTD_ML_PAGE, ["utd-ms-cs"], UTD_ML_NOTE),
    ("utd", "Rishabh Iyer", "Assistant Professor",
     "optimization, submodular optimization, data efficient machine learning, robust learning, feature selection, data summarization",
     UTD_ML_PAGE, ["utd-ms-cs"], UTD_ML_NOTE),
    ("utd", "Vibhav Gogate", "Associate Professor; Co-Director, Center for Machine Learning",
     "artificial intelligence, machine learning, data mining, probabilistic graphical models, probabilistic programming",
     UTD_ML_PAGE, ["utd-ms-cs"], UTD_ML_NOTE),
    ("utd", "Nicholas Ruozzi", "Associate Professor",
     "statistical machine learning, probabilistic graphical models, approximate inference, optimization",
     UTD_ML_PAGE, ["utd-ms-cs"], UTD_ML_NOTE),
    ("utd", "Feng Chen", "Associate Professor",
     "data mining, network mining, machine learning, event and pattern detection",
     UTD_ML_PAGE, ["utd-ms-cs"], UTD_ML_NOTE),
    ("utd", "Yu Xiang", "Assistant Professor", "robotics, computer vision, robot learning",
     UTD_ML_PAGE, ["utd-ms-cs"], UTD_ML_NOTE),
    ("ut", "Kristen Grauman", "Professor", "machine learning", UT_PROFILE + "kristen-grauman", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "Peter Stone", "Head of School and Professor", "machine learning", UT_PROFILE + "peter-stone", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "Inderjit Dhillon", "Professor", "machine learning", UT_PROFILE + "inderjit-dhillon", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "Adam Klivans", "Professor", "machine learning", UT_PROFILE + "adam-klivans", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "Risto Miikkulainen", "Professor", "machine learning", UT_PROFILE + "risto-miikkulainen", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "Yuke Zhu", "Associate Professor", "machine learning", UT_PROFILE + "yuke-zhu", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "Philipp Krähenbühl", "Associate Professor", "machine learning", UT_PROFILE + "philipp-krahenbuhl", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
    ("ut", "David Harwath", "Assistant Professor", "machine learning", UT_PROFILE + "david-harwath", ["ut-ms-cs", "ut-phd-cs"], UT_ML_NOTE),
]

FUNDING = [
    {
        "name": "NSF Graduate Research Fellowship (GRFP)",
        "funding_type": "fellowship",
        "university": None,
        "provider": "U.S. National Science Foundation",
        "description": (
            "Supports students in research-based master's and doctoral programs in STEM fields, including "
            "computer and information science. Three years of support usable over a five-year period."
        ),
        "eligibility": (
            "U.S. citizens, nationals and permanent residents in an eligible STEM field who have completed less "
            "than one academic year of graduate study. Applications are due each October (the 2026 deadline for "
            "Computer and Information Science and Engineering was October 20, 2026)."
        ),
        "amount": 37000,
        "amount_note": "per year stipend for 3 years, plus a $16,000 cost-of-education allowance to the university",
        "covers_tuition": True,
        "international_eligible": False,
        "degree_levels": "masters,doctoral",
        "deadline": None,
        "url": "https://www.nsf.gov/funding/opportunities/grfp-nsf-graduate-research-fellowship-program/nsf26-526/solicitation",
    },
    {
        "name": "Fulbright Foreign Student Program",
        "funding_type": "scholarship",
        "university": None,
        "provider": "U.S. Department of State",
        "description": (
            "About 4,000 grants each year for international students to study for a master's or doctoral degree "
            "and conduct research at U.S. universities."
        ),
        "eligibility": (
            "Non-U.S. citizens. Eligibility, award benefits, deadlines and university placement vary by country; "
            "apply through the Fulbright Commission/Foundation or U.S. Embassy in your home country."
        ),
        "amount": None,
        "amount_note": "benefits vary by country",
        "covers_tuition": False,
        "international_eligible": True,
        "degree_levels": "masters,doctoral",
        "deadline": None,
        "url": "https://foreign.fulbrightonline.org/apply",
    },
    {
        "name": "UT Dallas Computer Science Teaching Assistantships",
        "funding_type": "assistantship",
        "university": "utd",
        "provider": "",
        "description": "Teaching assistant positions in the UT Dallas Department of Computer Science.",
        "eligibility": (
            "Most teaching assistantships are offered to students admitted to start in fall semesters; admitted "
            "students are told about any TA support after admission. See the department's admissions FAQ."
        ),
        "amount": None,
        "amount_note": "",
        "covers_tuition": False,
        "international_eligible": True,
        "degree_levels": "",
        "deadline": None,
        "url": "https://cs.utdallas.edu/admissions/admissions-faq",
    },
]


class Command(BaseCommand):
    help = "Load GradApp's verified real starter data and remove old fictional sample records."

    @transaction.atomic
    def handle(self, *args, **options):
        removed = self.remove_sample_data()
        verified_at = timezone.make_aware(datetime.combine(VERIFIED_ON, time(12)))

        universities = {}
        for data in UNIVERSITIES:
            data = dict(data)
            key = data.pop("key")
            university, created = University.objects.get_or_create(name=data["name"], defaults=data)
            if not created and (".example" in university.website_url or not university.website_url):
                university.website_url = data["website_url"]
                university.save(update_fields=["website_url"])
            universities[key] = university

        programs = {}
        for data in PROGRAMS:
            data = dict(data)
            key = data.pop("key")
            university = universities[data.pop("university")]
            program = GraduateProgram.objects.filter(
                university=university, name=data["name"], degree_level=data["degree_level"]
            ).first()
            values = {
                **data,
                "tuition_per_year": None,
                "funding_available": False,
                "origin": "admin",
                "needs_review": False,
                "is_active": True,
                "source_retrieved_at": verified_at,
            }
            if program is None:
                program = GraduateProgram.objects.create(university=university, **values)
            elif program.source_retrieved_at is None or program.source_retrieved_at <= verified_at:
                # Never overwrite information refreshed after this dataset was verified.
                for field, value in values.items():
                    setattr(program, field, value)
                program.save()
            programs[key] = program

        for university_key, name, title, areas, profile_url, program_keys, bio in FACULTY:
            member, _ = Faculty.objects.update_or_create(
                university=universities[university_key],
                name=name,
                defaults={
                    "title": title,
                    "department": "Department of Computer Science",
                    "research_areas": areas,
                    "profile_url": profile_url,
                    "bio": bio,
                    "accepting_students": None,
                    "origin": "admin",
                    "needs_review": False,
                    "is_active": True,
                },
            )
            member.programs.set([programs[key] for key in program_keys])

        for data in FUNDING:
            data = dict(data)
            university_key = data.pop("university")
            FundingOpportunity.objects.update_or_create(
                name=data["name"],
                defaults={
                    **data,
                    "university": universities[university_key] if university_key else None,
                    "provider": data["provider"] or (universities[university_key].name if university_key else ""),
                    "origin": "admin",
                    "needs_review": False,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Real data ready (verified {VERIFIED_ON:%B %d, %Y}): {len(universities)} universities, "
            f"{len(PROGRAMS)} programs, {len(FACULTY)} faculty, {len(FUNDING)} funding opportunities."
            + (f" Removed {removed} old sample records." if removed else "")
        ))

    @staticmethod
    def remove_sample_data():
        """Delete fictional records created by earlier versions (".example" addresses)."""
        removed = 0
        for model in (FundingOpportunity, Faculty, GraduateProgram):
            count, _ = model.objects.filter(origin="sample").delete()
            removed += count
        count, _ = University.objects.filter(website_url__contains=".example").delete()
        removed += count
        # Iteration 1 placeholder programs (real university names, invented numbers).
        GraduateProgram.objects.filter(description="Sample record for Iteration 1 testing.").update(is_active=False)
        return removed
