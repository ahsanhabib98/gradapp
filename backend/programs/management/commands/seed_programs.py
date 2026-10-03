from datetime import date

from django.core.management.base import BaseCommand

from programs.models import GraduateProgram, University


SAMPLE_DATA = [
    {
        "university": {
            "name": "Texas A&M University-Corpus Christi",
            "city": "Corpus Christi",
            "state_or_region": "Texas",
            "country": "United States",
            "website_url": "https://www.tamucc.edu/",
        },
        "program": {
            "name": "Computer Science",
            "degree_level": "masters",
            "field_of_study": "Computer Science",
            "description": "Sample record for Iteration 1 testing.",
            "admission_requirements": "Verify current requirements on the official program website.",
            "tuition_per_year": 18000,
            "funding_available": True,
            "funding_details": "Assistantships may be available. Verify with the department.",
            "application_deadline": date(2027, 2, 1),
            "program_url": "https://www.tamucc.edu/",
        },
    },
    {
        "university": {
            "name": "University of Houston",
            "city": "Houston",
            "state_or_region": "Texas",
            "country": "United States",
            "website_url": "https://www.uh.edu/",
        },
        "program": {
            "name": "Computer Science",
            "degree_level": "doctoral",
            "field_of_study": "Computer Science",
            "description": "Sample record for Iteration 1 testing.",
            "admission_requirements": "Verify current requirements on the official program website.",
            "tuition_per_year": 26000,
            "funding_available": True,
            "funding_details": "Funding varies by appointment and availability.",
            "application_deadline": date(2026, 12, 1),
            "program_url": "https://www.uh.edu/",
        },
    },
]


class Command(BaseCommand):
    help = "Create a small, repeatable sample program dataset for Iteration 1."

    def handle(self, *args, **options):
        for item in SAMPLE_DATA:
            university_data = item["university"]
            university, _ = University.objects.update_or_create(
                name=university_data["name"], defaults=university_data
            )
            program_data = item["program"]
            GraduateProgram.objects.update_or_create(
                university=university,
                name=program_data["name"],
                degree_level=program_data["degree_level"],
                defaults=program_data,
            )
        self.stdout.write(self.style.SUCCESS("Sample GradApp programs created."))
