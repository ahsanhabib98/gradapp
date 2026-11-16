# GradApp

GradApp helps prospective graduate students discover programs, get personalized
recommendations, find potential advisors and funding, compare options, and track
application deadlines. It is built by team **DevCave** for COSC 6370 (Advanced Software Engineering).

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router, Vite, served by nginx |
| Backend | Django 5 + Django REST Framework, JWT authentication |
| Database | PostgreSQL 17 (SQLite for local development and tests) |
| AI | OpenAI API (optional, with rule-based fallback) |

## Quick start (Docker)

```bash
cp .env.example .env      # then edit secrets; optionally add OPENAI_API_KEY
docker compose up --build
```

- App: http://localhost:3000
- API: http://localhost:8000/api/
- Data admin (Django admin): http://localhost:8000/admin/

With the defaults in `.env.example`, the backend applies migrations, loads GradApp's **verified real
starter data**, and creates an administrator account from `DJANGO_SUPERUSER_*`. Sign in with that
account to see the administrator features (Manage Users, Retrieve Program Information).

Stop with `docker compose down` (add `--volumes` to delete the database).

## Deploying online for free

See **[DEPLOY.md](DEPLOY.md)**: backend and frontend on Render (free plan) with a free Neon PostgreSQL
database, using the included `render.yaml` Blueprint.

## Use case coverage

Every use case in the GradApp use case diagram is implemented:

| Use case | Actor | Backend | Frontend |
|---|---|---|---|
| Register/Login | GradApp User | `POST /api/auth/register/`, `/login/`, `/token/refresh/`, `/logout/` | Sign-in screen |
| Create Academic/Student Profile | GradApp User | `GET/PATCH /api/auth/profile/` | **Profile** page |
| Search Graduate Programs | GradApp User | `GET /api/programs/?search=` | **Discover** page |
| Advanced Search/Filter «extend» | GradApp User | degree, funding, tuition, region, open deadline and sort filters | Discover filters panel |
| Retrieve Program Information «include» | External University Websites, Administrator | `programs/retrieval.py`; `POST /api/programs/{id}/retrieve/`; `manage.py retrieve_programs`; admin action | "Last verified" badges; admin retrieval panel on program details |
| Get Personalized Recommendations | GradApp User | `GET /api/recommendations/` | **For you** page |
| View Faculty Profiles | GradApp User | `GET /api/faculty/` (`?match_profile=true` ranks advisors) | **Faculty** page, faculty on program details |
| Search Funding | GradApp User | `GET /api/funding/` | **Funding** page |
| Save Programs | GradApp User | `/api/saved-programs/` | Save buttons, **Saved** page |
| Track Application Deadlines | GradApp User | `GET /api/deadlines/` | **Deadlines** page |
| Ask AI Questions | GradApp User | `/api/conversations/` (saved chats), `POST /api/conversations/{id}/messages/`, `POST /api/ai/ask/` | **Ask AI** page with saved chats and web search |
| Compare Programs | GradApp User | `GET /api/programs/compare/?ids=` | Compare buttons, tray, **Compare** page |
| View Program Details | GradApp User | `GET /api/programs/{id}/` (+ `/similar/`) | Program details page |
| Manage Users | GradApp Administrator | `/api/admin/users/` | **Users** page (administrators only) |

### How "Search includes Retrieve Program Information" is realized

Fetching university websites live on every search would be slow and fragile, and it would hammer
university servers. GradApp therefore retrieves program information ahead of time and caches it:

1. An administrator (or a scheduled `manage.py retrieve_programs --stale` job) fetches each program's
   official page.
2. `programs/retrieval.py` checks the URL is public and allowed by `robots.txt`, extracts tuition,
   deadline, minimum GPA, funding and requirements (with OpenAI when configured, otherwise
   rule-based), updates the program, and stores a dated `SourceSnapshot`.
3. Search and details read the cached data and show a **Verified / Not yet verified / Verified over
   90 days ago** badge, so students know how fresh each record is.

## AI features

Set `OPENAI_API_KEY` in `.env` to enable AI. `OPENAI_MODEL` defaults to `gpt-6-luna`, OpenAI's low-cost
model; change it to any chat model your key can access (for example `gpt-6.1-sol` for higher quality).
After changing `.env`, restart the backend: `docker compose up -d backend`.

| Feature | With API key | Without API key |
|---|---|---|
| Ask AI Questions | Answers from GradApp records (cited as `[P3]`, `[F7]`, `[G2]`); searches the web when they can't answer | Lists the best-matching records |
| Web search fallback | OpenAI `web_search` tool; answer cites web sources as `[W1]`; found programs, funding and faculty are saved to GradApp | Not available |
| Recommendations | Rule-based fit score plus a short AI summary | Rule-based fit score with reasons |
| Retrieve Program Information | AI extraction of facts from the page | Pattern-based extraction |

### Ask AI: saved chats and web search

- **Saved conversations:** every chat is stored on the server. Students can start a **New chat** or reopen
  any previous one from the sidebar and continue it; follow-up questions use the earlier turns as context.
  Chats can be deleted from the sidebar.
- **GradApp first, then the web:** the assistant answers from GradApp's records. If no records match, or
  the model reports that the records cannot answer (it replies `NO_ANSWER`), GradApp searches the web with
  OpenAI's built-in `web_search` tool. Students can also press **Search web** to go straight to the web.
- **Saving what was found:** a second AI call extracts the programs, funding and faculty described in the
  web answer. Each one is saved **only** if its source URL is one the search actually cited. Saved
  records are marked `origin = web` and `needs_review = true`, and they show a **"From web search · not yet
  reviewed"** badge everywhere until an administrator approves them in the data admin (filter by
  *needs review*, then use the **Mark selected records as reviewed** action). Existing records are never
  changed by web search.
- Web search uses extra OpenAI calls and costs more than normal answers. Set `AI_WEB_SEARCH_ENABLED=false`
  to turn it off.

Recommendations score **fit, not admission chances**. Each score is broken down into academic fit
(35), location (15), budget (15), funding (15), GPA (10) and timing (10), and every point comes with a
plain-language reason or caution. AI answers are grounded in database records to limit hallucination,
and the UI always links to the source records and official sites.

## Starter data (real, verified)

`manage.py seed_programs` loads real records copied from official university and funder pages and checked
on November 16, 2026:

- **9 programs** at Texas A&M University-Corpus Christi, the University of Houston, UT Dallas and UT Austin
  (MS and PhD in Computer Science, MS/PhD in Software Engineering, MS in Statistics & Data Science)
- **20 faculty** from official department research pages, linked to their programs
- **3 funding opportunities**: NSF Graduate Research Fellowship, Fulbright Foreign Student Program, and UT Dallas
  CS teaching assistantships

Every link points to the official page the facts came from. Facts an official page did not state (often tuition)
are left empty rather than estimated. Running the command also removes the fictional "(Sample)" records created
by earlier versions. Deadlines change every year, so records show "Verified over 90 days ago" once they need a
recheck. Set `SEED_SAMPLE_DATA=false` to skip loading this data.

When Ask AI finds new programs, faculty or funding on the web, it saves them only if the link is on the
university's (or funder's) own website, is not a rankings/aggregator site, and actually loads.

## Development without Docker

Backend (see `backend/README.md`):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=true
python manage.py migrate && python manage.py seed_programs && python manage.py createsuperuser
python manage.py runserver
```

Frontend (see `frontend/README.md`):

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

## Tests

```bash
cd backend && python manage.py test     # 83 API, service and regression tests
cd frontend && npm test                 # 12 API client, profile and chat tests
```

## Security notes

- `.env` is git-ignored; only `.env.example` is committed.
- `DJANGO_DEBUG` defaults to `false`, and the server refuses to start without `DJANGO_SECRET_KEY` in that mode.
- Login and registration are rate-limited (`THROTTLE_AUTH`), as are AI questions (`THROTTLE_AI`).
- Access tokens last 30 minutes. Refresh tokens are rotated and blacklisted on logout.
- The retrieval service blocks private and loopback addresses (SSRF protection), validates every
  redirect hop, honours `robots.txt`, and limits response size and time.
- The backend container runs as a non-root user; static files are served by WhiteNoise.
- JWTs are kept in `localStorage`, which is simple but exposes them to XSS. Moving to httpOnly
  cookies is a recommended hardening step before any public deployment.
