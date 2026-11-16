from datetime import date
from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gradapp.testutils import make_faculty, make_funding, make_program, make_university, make_user

from .models import GraduateProgram, SourceSnapshot
from .retrieval import RetrievalBlocked, extract_with_rules, html_to_text, retrieve_program_information, validate_public_url


class ProgramApiTests(APITestCase):
    def setUp(self):
        self.user = make_user("student", research_interests="machine learning")
        self.admin = make_user("admin", staff=True)
        self.university = make_university()
        self.program = make_program(self.university, "Data Science", funding_available=True)
        self.other_university = make_university("Northern University", city="Toronto", state="Ontario", country="Canada")
        self.cs = make_program(self.other_university, "Computer Science", tuition_per_year=35000, days=-5)

    def list(self, **params):
        self.client.force_authenticate(user=self.user)
        return self.client.get(reverse("program-list"), params)

    def test_program_list_requires_authentication(self):
        response = self.client.get(reverse("program-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_search_and_filter(self):
        response = self.list(search="Data", degree_level="masters", funding_available="true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_multi_word_search_matches_across_fields(self):
        response = self.list(search="computer toronto")
        self.assertEqual([p["name"] for p in response.data["results"]], ["Computer Science"])

    def test_invalid_max_tuition_returns_400_not_500(self):
        response = self.list(max_tuition="abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valid number", response.data["error"]["message"])

    def test_max_tuition_and_open_deadline_filters(self):
        self.assertEqual(self.list(max_tuition="25000").data["count"], 1)
        self.assertEqual(self.list(deadline_open="true").data["count"], 1)

    def test_funding_filter_counts_linked_funding_opportunities(self):
        make_funding(program=self.cs, university=self.other_university)
        self.assertEqual(self.list(funding_available="true").data["count"], 2)

    def test_program_reports_saved_and_stale_state(self):
        data = self.list(search="Data").data["results"][0]
        self.assertFalse(data["is_saved"])
        self.assertTrue(data["is_stale"])

    def test_regular_user_cannot_create_program(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("program-list"),
            {"university_id": self.university.id, "name": "AI", "degree_level": "masters", "field_of_study": "AI", "program_url": "https://example.edu/ai"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_program(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("program-list"),
            {"university_id": self.university.id, "name": "AI", "degree_level": "masters", "field_of_study": "AI", "program_url": "https://example.edu/ai"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_compare_programs(self):
        make_faculty(self.university, programs=[self.program])
        make_funding(program=self.program, university=self.university)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("program-compare"), {"ids": f"{self.program.id},{self.cs.id}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first = response.data["results"][0]
        self.assertEqual(first["id"], self.program.id)
        self.assertEqual(first["faculty_count"], 1)
        self.assertEqual(first["top_research_areas"], ["machine learning", "robotics"])
        self.assertEqual(len(first["funding_opportunities"]), 1)

    def test_compare_requires_two_to_four_programs(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get(reverse("program-compare"), {"ids": str(self.program.id)}).status_code, 400)
        self.assertEqual(self.client.get(reverse("program-compare"), {"ids": f"{self.program.id},9999"}).status_code, 400)
        self.assertEqual(self.client.get(reverse("program-compare"), {"ids": "a,b"}).status_code, 400)

    def test_similar_programs(self):
        similar = make_program(self.other_university, "Applied Data Science")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("program-similar", args=[self.program.id]))
        self.assertEqual([p["id"] for p in response.data], [similar.id])


class FacultyApiTests(APITestCase):
    def setUp(self):
        self.university = make_university()
        self.program = make_program(self.university)
        self.ml = make_faculty(self.university, "Dr. Learner", "machine learning, computer vision", [self.program], accepting_students=True)
        self.bio = make_faculty(self.university, "Dr. Ocean", "marine ecology, fisheries")

    def test_search_and_filter_faculty(self):
        self.client.force_authenticate(make_user())
        response = self.client.get(reverse("faculty-list"), {"search": "vision"})
        self.assertEqual([f["name"] for f in response.data["results"]], ["Dr. Learner"])
        response = self.client.get(reverse("faculty-list"), {"program": self.program.id, "accepting_students": "true"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["research_area_list"], ["machine learning", "computer vision"])

    def test_match_profile_ranks_potential_advisors(self):
        self.client.force_authenticate(make_user(research_interests="computer vision and robots"))
        response = self.client.get(reverse("faculty-list"), {"match_profile": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([f["name"] for f in response.data["results"]], ["Dr. Learner"])
        self.assertIn("computer vision", response.data["results"][0]["matched_areas"])
        self.assertGreater(response.data["results"][0]["match_score"], 0)

    def test_match_profile_requires_interests(self):
        self.client.force_authenticate(make_user())
        response = self.client.get(reverse("faculty-list"), {"match_profile": "true"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FundingApiTests(APITestCase):
    def setUp(self):
        self.university = make_university()
        self.program = make_program(self.university)
        self.ta = make_funding("Teaching Assistantship", self.university, self.program, days=10)
        self.university_wide = make_funding("University Scholarship", self.university, None, funding_type="scholarship", amount=5000, international_eligible=False)
        self.closed = make_funding("Closed Fellowship", self.university, None, days=-1, funding_type="fellowship")
        self.client.force_authenticate(make_user())

    def names(self, **params):
        return sorted(f["name"] for f in self.client.get(reverse("funding-list"), params).data["results"])

    def test_open_only_by_default(self):
        self.assertEqual(self.names(), ["Teaching Assistantship", "University Scholarship"])
        self.assertIn("Closed Fellowship", self.names(open_only="false"))

    def test_filters(self):
        self.assertEqual(self.names(funding_type="scholarship"), ["University Scholarship"])
        self.assertEqual(self.names(international_eligible="true"), ["Teaching Assistantship"])
        self.assertEqual(self.names(min_amount="10000"), ["Teaching Assistantship"])
        self.assertEqual(self.names(program=self.program.id), ["Teaching Assistantship", "University Scholarship"])

    def test_days_left_reported(self):
        item = self.client.get(reverse("funding-detail", args=[self.ta.id])).data
        self.assertEqual(item["days_left"], 10)
        self.assertTrue(item["is_open"])


SAMPLE_HTML = """
<html><head><title>MS in Data Science | Example University</title><script>var x=1;</script></head>
<body><nav>Menu</nav><main>
<h1>Master of Science in Data Science</h1>
<p>Tuition for full-time students is $21,450 per year.</p>
<p>The application deadline for fall admission is February 15, 2027.</p>
<p>Applicants need a minimum GPA of 3.25 on a 4.0 scale.</p>
<p>Graduate assistantships are available for qualified students.</p>
<h2>Admission Requirements</h2>
<p>Bachelor's degree in a quantitative field</p>
</main><footer>Footer</footer></body></html>
"""


class RetrievalTests(APITestCase):
    def setUp(self):
        self.university = make_university()
        self.program = make_program(self.university, tuition_per_year=None, application_deadline=None)

    def test_html_to_text_strips_navigation_and_scripts(self):
        title, text = html_to_text(SAMPLE_HTML)
        self.assertEqual(title, "MS in Data Science | Example University")
        self.assertNotIn("Menu", text)
        self.assertNotIn("var x", text)

    def test_rule_based_extraction(self):
        _, text = html_to_text(SAMPLE_HTML)
        facts = extract_with_rules(text)
        self.assertEqual(facts["tuition_per_year"], "21450")
        self.assertEqual(facts["application_deadline"], "2027-02-15")
        self.assertEqual(facts["minimum_gpa"], "3.25")
        self.assertTrue(facts["funding_available"])
        self.assertIn("quantitative", facts["admission_requirements"])

    @mock.patch("programs.retrieval.fetch_html", return_value=(200, SAMPLE_HTML))
    def test_retrieval_updates_program_and_records_snapshot(self, _fetch):
        snapshot = retrieve_program_information(self.program)
        self.program.refresh_from_db()
        self.assertEqual(snapshot.status, SourceSnapshot.Status.SUCCESS)
        self.assertEqual(snapshot.extraction_method, "rules")
        self.assertEqual(str(self.program.tuition_per_year), "21450.00")
        self.assertEqual(self.program.application_deadline, date(2027, 2, 15))
        self.assertIsNotNone(self.program.source_retrieved_at)
        self.assertFalse(self.program.is_stale)
        self.assertIn("tuition_per_year", snapshot.applied_fields)

    @mock.patch("programs.retrieval.fetch_html", return_value=(200, SAMPLE_HTML))
    def test_retrieval_uses_ai_extraction_when_available(self, _fetch):
        reply = '{"tuition_per_year": 19999, "application_deadline": "2027-03-01", "minimum_gpa": null}'
        with mock.patch("programs.retrieval.llm.is_configured", return_value=True), \
             mock.patch("programs.retrieval.llm.complete", return_value=reply):
            snapshot = retrieve_program_information(self.program)
        self.program.refresh_from_db()
        self.assertEqual(snapshot.extraction_method, "ai")
        self.assertEqual(self.program.application_deadline, date(2027, 3, 1))

    def test_private_addresses_are_blocked(self):
        for url in ("http://127.0.0.1/admin", "http://localhost:8000/", "ftp://example.edu/", "http://10.0.0.5/"):
            with self.assertRaises(RetrievalBlocked):
                validate_public_url(url)

    def test_blocked_url_recorded_as_snapshot(self):
        self.program.program_url = "http://127.0.0.1/secret"
        self.program.save()
        snapshot = retrieve_program_information(self.program)
        self.assertEqual(snapshot.status, SourceSnapshot.Status.BLOCKED)
        self.program.refresh_from_db()
        self.assertIsNone(self.program.source_retrieved_at)

    def test_robots_txt_is_respected(self):
        session = mock.Mock()
        session.headers = {}
        session.get.return_value = mock.Mock(status_code=200, text="User-agent: *\nDisallow: /")
        with mock.patch("programs.retrieval.validate_public_url"):
            from .retrieval import fetch_html
            with self.assertRaises(RetrievalBlocked):
                fetch_html("https://example.edu/program", session=session)

    def test_only_admins_can_trigger_retrieval(self):
        self.client.force_authenticate(make_user())
        response = self.client.post(reverse("program-retrieve-information", args=[self.program.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch("programs.retrieval.fetch_html", return_value=(200, SAMPLE_HTML))
    def test_admin_retrieval_endpoint(self, _fetch):
        self.client.force_authenticate(make_user("admin", staff=True))
        response = self.client.post(reverse("program-retrieve-information", args=[self.program.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["snapshot"]["status"], "success")
        self.assertEqual(response.data["program"]["tuition_per_year"], "21450.00")
        sources = self.client.get(reverse("program-sources", args=[self.program.id]))
        self.assertEqual(len(sources.data), 1)


class SeedCommandTests(APITestCase):
    def seed(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_programs", stdout=StringIO())

    def test_seed_loads_only_real_records_with_official_links(self):
        from .models import Faculty, FundingOpportunity

        self.seed()
        self.seed()  # repeatable
        self.assertEqual(GraduateProgram.objects.count(), 9)
        self.assertEqual(Faculty.objects.count(), 20)
        self.assertEqual(FundingOpportunity.objects.count(), 3)
        urls = [p.program_url for p in GraduateProgram.objects.all()]
        urls += [p.university.website_url for p in GraduateProgram.objects.select_related("university")]
        urls += [f.profile_url for f in Faculty.objects.all()] + [f.url for f in FundingOpportunity.objects.all()]
        for url in urls:
            self.assertTrue(url.startswith("https://"), url)
            self.assertNotIn(".example", url)
        for program in GraduateProgram.objects.all():
            self.assertNotIn("(Sample)", program.university.name)
            self.assertIsNotNone(program.source_retrieved_at)
            self.assertFalse(program.needs_review)
        houston = GraduateProgram.objects.get(university__name="University of Houston", degree_level="masters", name="Computer Science")
        self.assertEqual(houston.faculty.count(), 6)

    def test_seed_removes_old_sample_records(self):
        from .models import University

        sample = University.objects.create(
            name="Gulf Coast State University (Sample)", city="Corpus Christi", state_or_region="Texas",
            website_url="https://www.gulfcoast-state.example/",
        )
        make_program(sample, "Marine Biology", origin="sample", program_url="https://www.gulfcoast-state.example/x")
        self.seed()
        self.assertFalse(University.objects.filter(name__contains="(Sample)").exists())
        self.assertFalse(GraduateProgram.objects.filter(program_url__contains=".example").exists())

    def test_seed_does_not_overwrite_newer_real_data(self):
        from django.utils import timezone

        self.seed()
        program = GraduateProgram.objects.get(university__name="University of Houston", degree_level="masters", name="Computer Science")
        program.tuition_per_year = 12345
        program.source_retrieved_at = timezone.now() + timezone.timedelta(days=1)
        program.save()
        self.seed()
        program.refresh_from_db()
        self.assertEqual(str(program.tuition_per_year), "12345.00")
