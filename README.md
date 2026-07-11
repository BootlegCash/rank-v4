# After Hours Ranked

After Hours Ranked is a Django-powered drinking leaderboard and social stats app. It lets users track drinks, earn XP, climb monthly/yearly/lifetime ranks, unlock achievements, manage friends, and view progress through a web interface and authenticated API.

The project is built for the `afterhoursranked.com` / Render deployment, with local development supported through SQLite and a simple `.env` file.

> Responsible-use note: this app is intended for adults of legal drinking age. It should be used as a social stats/game layer, not as encouragement to drink excessively or unsafely.

## What it does

- Tracks drink totals for beer/seltzer, Floco, rum, whiskey, vodka, tequila, shotguns, snorkels, and throw-up penalties.
- Calculates XP from alcohol totals, bonuses, and penalties.
- Maintains three rank systems:
  - monthly ranks that reset each calendar month
  - yearly ranks that reset each calendar year
  - lifetime sub-ranks from Bronze through Steeze
- Uses a Phoenix-time daily log window where a “day” runs from 4 AM to 4 AM.
- Supports profiles, display names, friends, friend requests, posts, likes, achievements, and token transactions.
- Provides Django template pages plus Django REST Framework API endpoints for authenticated clients.
- Sends password/account emails through Resend SMTP in production, with console email output locally when no API key is configured.
- Ships with Render deployment configuration via `render.yaml`.

## Tech stack

- Python 3.10+
- Django 4.2
- Django REST Framework
- Simple JWT / DRF auth token support
- django-cors-headers
- django-jazzmin admin theme
- WhiteNoise for static files
- SQLite for local development
- PostgreSQL-compatible `DATABASE_URL` support through `dj-database-url`
- Gunicorn for production serving
- Render for deployment

## Project structure

```text
.
├── accounts/          # profiles, logs, friends, posts, API endpoints, templates
├── achievements/      # achievement models, data, and import command
├── myapp/             # Django project settings, URL config, WSGI/ASGI
├── templates/         # shared/admin template overrides
├── testing/           # local testing helpers
├── tests/             # mock/test helpers
├── manage.py
├── requirements.txt
├── render.yaml
└── .env.example
```

## Local setup

### 1. Clone the repo

```bash
git clone https://github.com/BootlegCash/rank-v4.git
cd rank-v4
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your environment file

```bash
cp .env.example .env
```

For local development, the defaults in `.env.example` are enough to run with SQLite and console email output.

Key environment variables:

| Variable | Purpose |
| --- | --- |
| `DEBUG` | Set to `True` locally and `False` in production. |
| `DJANGO_ENV` | Use `development` locally and `production` on Render. |
| `SECRET_KEY` | Django secret key. Use a real secret outside local development. |
| `DATABASE_URL` | Database connection string. Defaults to local SQLite. |
| `RESEND_API_KEY` | Resend SMTP key. Required in production. |
| `RESEND_FROM_EMAIL` | Sender used for account/password emails. |
| `SITE_DOMAIN` | Domain used when building absolute links in emails. |

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

### 7. Start the server

```bash
python manage.py runserver
```

Then open:

- App: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

## Useful commands

Import achievement data, if needed:

```bash
python manage.py import_achievements
```

Populate demo data, if using the included demo command:

```bash
python manage.py populate_demo
```

Run Django checks:

```bash
python manage.py check
```

Run tests:

```bash
python manage.py test
```

## API overview

The project uses Django REST Framework and authenticated endpoints under the accounts API routes. The project URL config includes token auth at:

```text
/api/token/
```

Core API behavior includes:

- current-user profile summary
- XP, monthly XP, yearly XP, and next-rank progress
- friend list/search/request flows
- daily log data
- posts and likes
- token balances and transactions

Most API routes require authentication by default.

## Ranking and XP model

XP is calculated from drink totals with bonuses and penalties:

- drink alcohol volume contributes XP
- shotguns and snorkels add bonus XP
- throw-up entries subtract XP
- XP never drops below zero

The app keeps separate progress tracks for:

- lifetime rank
- monthly rank
- yearly rank

Daily logs are grouped using the app’s custom day boundary: 4 AM to 4 AM in the America/Phoenix timezone.

## Deployment

This repo includes `render.yaml` for Render:

```yaml
buildCommand: pip install -r requirements.txt
startCommand: gunicorn myapp.wsgi:application
```

Production expects:

- `DJANGO_ENV=production`
- `DEBUG=False`
- a generated/secure `SECRET_KEY`
- `RESEND_API_KEY` configured for email delivery
- a production database URL if not using the default SQLite fallback

The Django settings already include allowed hosts and CSRF/CORS origins for:

- `afterhoursranked.com`
- `www.afterhoursranked.com`
- `ranked-0xtx.onrender.com`

## Development notes

Generated files such as virtual environments, bytecode caches, and local databases should generally stay out of source control. If you are cleaning up the repository, good follow-up candidates are:

- `.venv/`
- `__pycache__/`
- `*.pyc`
- local `db.sqlite3` files

Add those to `.gitignore` before removing them from the repo history or future commits.

## License

No license is currently specified. Add one before distributing or accepting outside contributions.
