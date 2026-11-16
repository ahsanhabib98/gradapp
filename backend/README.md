# GradApp Backend

Django REST API for GradApp: JWT authentication, student profiles, programs, faculty, funding,
saved programs and deadlines, recommendations, AI question answering, information retrieval, and
user management.

## Apps

| App | Responsibility |
|---|---|
| `accounts` | Registration, login/logout, student profile, Manage Users API |
| `programs` | Universities, programs, faculty, funding, source snapshots, retrieval service |
| `planner` | Saved programs (status, notes, target dates) and the deadlines timeline |
| `assistant` | Recommendation engine, AI question answering, saved conversations, web search fallback, OpenAI client |
| `gradapp` | Settings, URL routing, error format, pagination, shared text matching |

## API endpoints

All endpoints except health, register and login require `Authorization: Bearer <access token>`.
List endpoints are paginated (`?page=`, `?page_size=` up to 100).

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | API and database health |
| POST | `/api/auth/register/` | Create an account and empty profile |
| POST | `/api/auth/login/` | Obtain access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Rotate tokens |
| POST | `/api/auth/logout/` | Blacklist the caller's refresh token |
| GET | `/api/auth/me/` | Current user (includes `is_staff`) |
| GET/PATCH | `/api/auth/profile/` | Student profile |
| GET | `/api/programs/` | Search and filter programs |
| GET | `/api/programs/{id}/` | Program details |
| GET | `/api/programs/{id}/similar/` | Comparable programs |
| GET | `/api/programs/{id}/sources/` | Retrieval history |
| POST | `/api/programs/{id}/retrieve/` | Retrieve information from the official site (admin) |
| GET | `/api/programs/compare/?ids=1,2,3` | Compare 2 to 4 programs |
| GET | `/api/universities/` | Universities |
| GET | `/api/faculty/` | Faculty search (`search`, `research_area`, `university`, `program`, `accepting_students`, `match_profile`) |
| GET | `/api/funding/` | Funding search (`search`, `funding_type`, `degree_level`, `program`, `university`, `international_eligible`, `covers_tuition`, `min_amount`, `open_only`, `ordering`) |
| GET/POST | `/api/saved-programs/` | List or save programs |
| PATCH/DELETE | `/api/saved-programs/{id}/` | Update status, notes, target date, or remove |
| GET | `/api/deadlines/` | Combined application, personal and funding deadlines (`include_past`) |
| GET | `/api/recommendations/` | Ranked recommendations (`limit`, `explain`) |
| GET/POST | `/api/conversations/` | List saved chats or start a new one |
| GET/PATCH/DELETE | `/api/conversations/{id}/` | Open a chat with its messages, rename, or delete it |
| POST | `/api/conversations/{id}/messages/` | Ask in a chat (`question`, `use_profile`, `search_web`); both turns are saved |
| POST | `/api/ai/ask/` | Stateless question (`question`, `use_profile`, `history`, `search_web`) |
| GET | `/api/ai/status/` | Whether OpenAI and web search are enabled |
| GET/PATCH | `/api/admin/users/` | Manage users (admin): search, activate/deactivate, grant admin |

Program filters: `search` (multi-word), `degree_level`, `field`, `country`, `state_or_region`,
`university`, `funding_available`, `max_tuition`, `max_gpa_required`, `deadline_open`, and
`ordering` (`name`, `-name`, `tuition`, `-tuition`, `deadline`, `university`).

Write operations on programs, universities, faculty and funding are restricted to administrators.

### Error format

Every error uses the same shape, with a readable `message` for the UI:

```json
{"error": {"status": 400, "message": "Password confirm: Passwords do not match.", "details": {...}}}
```

## Management commands

```bash
python manage.py seed_programs                 # verified real starter data (idempotent)
python manage.py retrieve_programs 3 5         # retrieve specific programs
python manage.py retrieve_programs --stale     # retrieve missing or >90-day-old information
python manage.py retrieve_programs --all --dry-run
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_DEBUG` | `false` | Debug mode; must be `true` locally unless `DJANGO_SECRET_KEY` is set |
| `DJANGO_SECRET_KEY` | none | Required when debug is off |
| `DATABASE_URL` | none | Full PostgreSQL URL (e.g. Neon); takes precedence over `POSTGRES_*` |
| `POSTGRES_*` | none | Use PostgreSQL when `POSTGRES_HOST` is set, otherwise SQLite |
| `CSRF_TRUSTED_ORIGINS` | empty | HTTPS origins allowed to post forms (Django admin) |
| `HTTPS` | `false` | Mark cookies secure when served over HTTPS |
| `PORT` / `WEB_CONCURRENCY` | `8000` / `2` | Port and number of gunicorn workers (set by hosts such as Render) |
| `OPENAI_API_KEY` | empty | Enables AI-powered features |
| `OPENAI_MODEL` | `gpt-6-luna` | OpenAI chat model |
| `OPENAI_BASE_URL` | empty | Optional OpenAI-compatible endpoint |
| `AI_REASONING_TOKEN_HEADROOM` | `2000` | Extra output tokens for reasoning models |
| `AI_WEB_SEARCH_ENABLED` | `true` | Search the web when GradApp's records can't answer |
| `AI_WEB_SEARCH_TIMEOUT_SECONDS` | `90` | Time limit for one web search |
| `THROTTLE_AUTH` / `THROTTLE_AI` | `20/min` / `30/hour` | Rate limits |
| `RETRIEVAL_STALE_AFTER_DAYS` | `90` | When program information is flagged stale |
| `SEED_SAMPLE_DATA` | `false` | Docker entrypoint loads the verified real starter data when `true` |
| `AI_REQUIRE_LIVE_LINKS` | `true` | Only save web-search results whose official links load |
| `DJANGO_SUPERUSER_*` | empty | Docker entrypoint creates an administrator |

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=true
python manage.py migrate
python manage.py seed_programs
python manage.py createsuperuser
python manage.py runserver
```

## Tests

```bash
python manage.py test
```

83 tests cover authentication, profiles, user management, search and filters, compare, faculty
matching, funding search, retrieval (extraction, SSRF and robots.txt protection, AI extraction),
saved programs, deadlines, recommendations and AI Q&A. OpenAI calls are mocked, so tests need no API key
or network access.
