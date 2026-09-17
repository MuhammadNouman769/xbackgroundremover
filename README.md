# Xbg Remove

AI-powered background remover — a production-ready Django clone of the
"remove background" tool style shown in removal.ai, branded as **Xbg Remove**.

## Features

- Upload a JPG / PNG / WEBP image, drag-and-drop, or paste with Ctrl+V
- AI background removal (on-device, via `rembg` / U2-Net — no paid API),
  tuned for speed: fast `u2netp` model by default + auto-downscaling of
  large photos before inference + the model pre-loaded at server startup
  instead of on the visitor's first click (see "Why removal is slow" below)
- While processing, the visitor's own uploaded photo is shown on the page
  with a spinner overlay — so it's always clear the tool is working on
  *their* image, not a frozen page
- Replace the removed background with a solid colour or a custom image
- Login / Signup (Django auth) — guests can try once, logged-in users get a history page
- Full site pages: Home, About, Contact (saved to `/admin/`), Terms & Conditions, Privacy Policy
- Header + footer includes, one shared `base.html`, clean `templates/` structure
- `favicon.ico` (shows in the browser tab and in Google search results) + SVG logo
- Environment-driven settings (`.env`) — nothing sensitive hard-coded
- Whitenoise for static files + Gunicorn — ready to deploy behind Nginx
- Google Analytics / Google AdSense slots wired into `base.html` (just paste your IDs into `.env`, no code changes)
- Rotating file logging under `logs/django.log`
- Django admin panel to review every processed job and every contact message

## Project layout

```
xbg_remove/
├── manage.py
├── requirements.txt
├── .env                   # already filled in with a dev SECRET_KEY - ready to run
├── .env.example            # template, for when you set up a fresh server
├── core/                   # settings package: settings.py, urls.py, wsgi.py, asgi.py
├── apps/                   # every Django app lives here
│   ├── accounts/           # login / signup app (forms.py, views.py, urls.py, models.py)
│   ├── remover/            # background-removal app (models, views, utils.py = AI engine)
│   └── pages/              # About / Contact / Terms / Privacy (static content + contact form)
├── templates/              # ALL html pages, grouped by app in their own subfolder
│   ├── base.html
│   ├── includes/           # header.html + footer.html
│   ├── accounts/           # login.html, signup.html
│   ├── remover/            # home.html, result.html, history.html
│   └── pages/              # about.html, contact.html, terms.html, privacy.html
├── static/                 # css/js/img + favicon.ico
├── media/                  # uploaded + processed images (created at runtime)
└── logs/                   # django.log
```

Each app under `apps/` is registered in `core/settings.py` as
`apps.accounts` / `apps.remover` / `apps.pages`, and included in
`core/urls.py` the same way — so Python still finds them correctly
even though they no longer sit at the project root.

## Why background removal was slow, and what was fixed

If it still feels slow after these changes, it's almost always the
**very first** request after the server starts (the AI model has to
load into memory once per worker process) — every request after that
should be fast. What's already in place to keep it snappy:

1. **Lighter model by default** — `REMBG_MODEL=u2netp` in `.env` (a
   small, fast model) instead of the full `u2net` (~170MB, noticeably
   slower on CPU). You can switch back to `u2net` for slightly better
   edge quality on complex photos, at the cost of speed.
2. **Model pre-loaded at startup** — `apps/remover/apps.py` warms up
   the model in a background thread as soon as the server starts,
   instead of waiting for a real visitor's first upload.
3. **Large photos are downscaled before inference** — anything wider
   than `MAX_DIMENSION` (1600px, in `apps/remover/utils.py`) is shrunk
   first; a 12MP phone photo has far more pixels than the model needs,
   and this is usually the single biggest win for real uploads.
4. **Instant visual feedback** — the moment you submit, `home.html`
   shows *your own uploaded photo* with a spinner overlay ("Removing
   background from your image…") instead of a blank/frozen page, so
   it's clear something is happening even while the server works.

If it's still too slow on your server: check `logs/django.log` for
how long a request actually takes; if it's slow on *every* request
(not just the first), your server's CPU is likely the bottleneck —
`u2netp` on a small/shared CPU host can still take a few seconds.
Options from there: use a host with more CPU, or move processing to a
Celery worker so the request returns instantly and the page polls for
the result instead of blocking (not included here, to keep the
project simple — ask if you want this added).

## Setup (local development)

```bash
# 1. Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Environment file
# A working .env is already included with a dev SECRET_KEY, so you can
# run the project as-is. Before deploying, generate a new SECRET_KEY
# and update DEBUG / ALLOWED_HOSTS (see "Going live" below).

# 4. Database
python manage.py makemigrations
python manage.py migrate

# 5. Create an admin user (optional, for /admin/)
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Open **http://127.0.0.1:8000/** — upload an image and try it out.

> First background-removal request will download the `u2net` AI model
> (~170 MB) from GitHub and cache it under `~/.u2net/`. This needs
> internet access **once**; after that everything runs fully offline.

## Going live / running Google Ads

1. Set `DEBUG=False` and `SECRET_KEY` to a real secret in `.env`.
2. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your real domain.
3. Switch `DATABASES` in `settings.py` to Postgres for production traffic
   (SQLite is fine for testing, not for concurrent production load).
4. Run:
   ```bash
   python manage.py collectstatic
   gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
   ```
5. Put Nginx (or your host's load balancer) in front of gunicorn for TLS.
6. Once your Google Ads / AdSense account is approved, paste
   `GOOGLE_ANALYTICS_ID` and `GOOGLE_ADSENSE_CLIENT_ID` into `.env` —
   the tags are already wired into every page via `base.html`.
7. Make sure `/static/favicon.ico` is reachable — this is what shows in
   the browser tab and next to your listing in Google Search.

## Notes / next steps you may want later

- Add email verification on signup (currently instant login for lower friction).
- Add per-user daily upload limits / paid plans if you want to monetise beyond ads.
- Swap SQLite → PostgreSQL and add Redis + Celery if you want background
  processing (useful once traffic grows and removals shouldn't block the request).
