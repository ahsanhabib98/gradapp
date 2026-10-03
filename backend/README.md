# GradApp Backend

This folder contains the Django REST API for GradApp. It provides JWT authentication, student profiles, university and graduate-program records, program search and filtering, PostgreSQL support, Django administration, sample data, and automated API tests.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | Confirm that the API and database are available |
| POST | `/api/auth/register/` | Create a user account and empty student profile |
| POST | `/api/auth/login/` | Obtain access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh an access token |
| POST | `/api/auth/logout/` | Blacklist a refresh token |
| GET | `/api/auth/me/` | Return the authenticated user |
| GET/PATCH/PUT | `/api/auth/profile/` | Read or update the authenticated student's profile |
| GET | `/api/universities/` | List universities |
| GET | `/api/programs/` | List or filter graduate programs |
| GET | `/api/programs/{id}/` | Retrieve one program |

Program filters include `search`, `degree_level`, `field`, `country`, `state_or_region`, `funding_available`, `max_tuition`, and `ordering`.

Example:

```text
/api/programs/?search=computer&degree_level=masters&funding_available=true
```

## Local development without Docker

When `POSTGRES_HOST` is not set, Django uses SQLite for local development and tests.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_programs
python manage.py createsuperuser
python manage.py runserver
```

## Tests

```bash
python manage.py test
```

## Docker

The backend image exposes port 8000 and automatically waits for PostgreSQL and applies migrations. The project-level `docker-compose.yml` will connect this service to the React frontend and PostgreSQL database.

Never commit a real `.env` file, passwords, secret keys, or API credentials.
