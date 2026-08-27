# Masskan Backend

Django + Django REST Framework API for **Masskan** (مسكن) — an apartment
rental matchmaking platform connecting apartment seekers ("searchers") with
property owners ("landlords"). This backend implements every page/feature of
the Masskan frontend as a documented REST API: authentication, profiles,
listings, AI-powered search, messaging, visit scheduling, reviews,
neighborhood insights, subscriptions/pricing, and notifications.

This project is the API layer only — it does not modify or serve the
existing React frontend. It is built so any developer, reading only this
README and the code, can understand the whole system without asking anyone.

---

## Tech stack

| Concern              | Choice                                             |
|-----------------------|-----------------------------------------------------|
| Framework              | Django 5.2 + Django REST Framework                 |
| Auth                   | JWT (`djangorestframework-simplejwt`), access + refresh, rotation & blacklisting |
| Filtering               | `django-filter`                                    |
| CORS                   | `django-cors-headers`                              |
| Database (dev)          | SQLite                                             |
| Database (prod)         | PostgreSQL                                         |
| Images/files             | Pillow, Django `ImageField`/`FileField`            |
| Config                  | `python-dotenv` + a `config/settings/{base,dev,prod}.py` split |
| WSGI/ASGI server (prod)  | gunicorn                                           |

---

## Project layout

```
config/
  settings/
    base.py        # shared settings — installed apps, DRF, JWT, CORS, logging
    dev.py          # SQLite, DEBUG=True, permissive CORS — local development
    prod.py         # Postgres, DEBUG=False, security headers — production
  urls.py           # mounts every app under /api/v1/<app>/
  wsgi.py / asgi.py

apps/
  common/           # cross-cutting utilities shared by every other app
    models.py         # TimeStampedModel abstract base
    pagination.py      # StandardResultsPagination (consistent envelope)
    permissions.py      # IsLandlord, IsSearcher, IsOwnerOrReadOnly, IsAdminRole, ReadOnly
    exceptions.py        # project-wide DRF exception handler -> {"error": {...}}
    services/
      notifications.py    # single call site for outbound email/SMS
    management/commands/
      seed_demo_data.py    # `python manage.py seed_demo_data`

  accounts/         # signup.tsx, signin.tsx, profile.tsx, reset-password.tsx,
                     # verify-email flows, landlord-profile.tsx, verification docs
  properties/       # search-results.tsx, apartment-details.tsx, add-listing.tsx,
                     # seller-dashboard.tsx listings, ai-search-questionnaire.tsx,
                     # admin-dashboard.tsx moderation
  areas/            # area-rating.tsx "Neighborhood Insights" panel
  reviews/          # property reviews (apartment-details.tsx) + landlord
                     # reviews with like-toggling (landlord-profile.tsx)
  messaging/        # chat.tsx — conversations & messages
  scheduling/        # schedule.tsx — visit/tour booking requests
  subscriptions/     # pricing-plans.tsx — plans, features, subscribe/cancel
  notifications/      # notification bell / "Notifications" tab on dashboards
```

Every app follows the same internal shape: `models.py`, `serializers.py`,
`views.py`, `urls.py`, `admin.py`, `migrations/`. Every view/serializer has a
docstring naming the exact frontend file it backs, so the mapping from
"what the user sees" to "what API serves it" is never a guessing game.

---

## Getting started

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # defaults work out of the box for dev

python manage.py migrate
python manage.py seed_demo_data     # optional — realistic demo data, see below
python manage.py createsuperuser    # optional — seed_demo_data already makes one

python manage.py runserver
```

The API is now at `http://127.0.0.1:8000/api/v1/`, and the Django admin at
`http://127.0.0.1:8000/admin/`.

### Demo data

`python manage.py seed_demo_data` populates amenities, three neighborhoods
(with nearby places), an admin + two landlords + two searchers, five
properties (mixed active/pending), all eight pricing plans with their
feature lists, property/landlord/area reviews, a sample conversation with
messages, a sample visit request, and a sample notification. It's safe to
run more than once — everything is `get_or_create`/`update_or_create`, so
re-running never duplicates data.

Seeded logins (password for all: `demo12345`):

| Role      | Email                          |
|-----------|----------------------------------|
| Admin      | `admin@masskan.app`               |
| Landlord   | `sarah.landlord@masskan.app`       |
| Landlord   | `michael.landlord@masskan.app`     |
| Searcher   | `amira.searcher@masskan.app`       |
| Searcher   | `omar.searcher@masskan.app`        |

### Running tests / checks

```bash
python manage.py check
python manage.py test
```

---

## Configuration

All configuration is environment-variable driven — see `.env.example` for
the full list with comments. Every variable has a safe development default
in `config/settings/dev.py`, so the project runs locally with an empty
`.env`. `config/settings/prod.py` requires the database and (recommended)
email variables to be set for real.

`DJANGO_SETTINGS_MODULE` selects which settings module loads:
`config.settings.dev` (default, via `manage.py`) or `config.settings.prod`
(default for `wsgi.py`/`asgi.py`, i.e. what a real deployment uses).

---

## Authentication

JWT, via `djangorestframework-simplejwt`. Access tokens last 60 minutes,
refresh tokens 14 days, with rotation-on-refresh and blacklisting of used
refresh tokens enabled.

```
POST /api/v1/accounts/register/         {email, username, password, password_confirm, role, first_name, last_name}
POST /api/v1/accounts/login/            {email, password}  -> {access, refresh, user}
POST /api/v1/accounts/login/refresh/    {refresh}          -> {access}
POST /api/v1/accounts/logout/           {refresh}          -> blacklists it
```

Authenticated requests send `Authorization: Bearer <access>`.

`role` is one of `searcher` / `landlord` (registration rejects `both` —
becoming "both" is an account upgrade, not a signup choice, matching the
frontend's flow).

---

## API reference

All endpoints are namespaced under `/api/v1/`. List endpoints are paginated
with the standard envelope unless noted "not paginated":

```json
{"count": 42, "total_pages": 4, "current_page": 1, "page_size": 12, "next": "...", "previous": null, "results": [...]}
```

Errors follow one consistent shape from every endpoint:

```json
{"error": {"code": "validation_error", "message": "A short summary.", "details": { ... }}}
```

### Accounts — `/api/v1/accounts/`

| Method & path | Purpose | Frontend page |
|---|---|---|
| `POST register/` | Create account, returns JWT pair immediately | signup.tsx |
| `POST login/`, `login/refresh/`, `logout/` | JWT auth | signin.tsx |
| `GET/PATCH me/` | View/update own profile | profile.tsx |
| `POST me/change-password/` | Change password while logged in | profile.tsx |
| `POST password-reset/` | Request reset email (always 200 — never leaks whether an email exists) | reset-password.tsx |
| `POST password-reset/confirm/` | Consume reset token, set new password | verified-password.tsx |
| `POST verify-email/resend/`, `POST verify-email/confirm/` | Email verification | signup.tsx / profile.tsx |
| `GET landlords/{user_id}/` | Public landlord profile, with aggregated rating/review/listing counts | landlord-profile.tsx |
| `GET/POST verification-documents/`, `POST verification-documents/{id}/review/` | Upload + admin-review ID/proof documents | profile.tsx, admin-dashboard.tsx |

Password reset and email verification use **stateless signed tokens**
(`apps/accounts/tokens.py`, built on Django's `PasswordResetTokenGenerator`)
rather than a database-backed token table — there's nothing to expire,
clean up, or leak.

### Properties — `/api/v1/properties/`

| Method & path | Purpose | Frontend page |
|---|---|---|
| `GET properties/` | Browse/search active listings — filters: `min_price`, `max_price`, `bedrooms`, `property_type`, `furnished`, `pet_friendly`, `near_public_transport`, `city`, `location`, `amenities` (comma-separated keys); `search=` full-text; `ordering=` | search-results.tsx |
| `GET properties/{id}/` | Listing detail (increments view count) | apartment-details.tsx |
| `POST properties/` | Create listing (landlord only, starts `pending`) | add-listing.tsx |
| `PATCH/PUT properties/{id}/` | Edit own listing (re-submits for approval if it was `active`) | add-listing.tsx (edit mode) |
| `DELETE properties/{id}/` | Delete own listing | seller-dashboard.tsx |
| `GET properties/featured/` | Featured grid (not paginated) | landing-page.tsx |
| `GET properties/mine/?status=` | My listings, any status | seller-dashboard.tsx |
| `POST properties/{id}/favorite/` | Toggle favorite | everywhere (heart icon) |
| `GET properties/favorites/` | My saved listings | profile.tsx / buyer-dashboard.tsx |
| `POST properties/{id}/images/` | Upload a listing photo (multipart, field `image`) | add-listing.tsx |
| `GET properties/pending/`, `POST properties/{id}/approve/`, `POST properties/{id}/reject/` | Moderation queue (admin only) | admin-dashboard.tsx |
| `GET properties/amenities/` | Amenity lookup list (not paginated) | add-listing.tsx / filters |
| `POST properties/ai-search/` | Weighted-match search from the 5-step questionnaire | ai-search-questionnaire.tsx -> ai-search-results.tsx |
| `GET properties/ai-search/history/` | My past AI-search submissions | ai-search-questionnaire.tsx |

**AI search** (`apps/properties/services.py`) is a transparent weighted
scorer, not a black box: budget fit (35pts), bedroom match (20), property
type (15), amenity overlap (15), pet-friendliness (10), transit access (5),
plus a base score (10) — capped at 100, with the point breakdown assembled
into a human-readable `match_reason` string on every result (e.g. *"Within
your budget · Has WiFi, Gym · Near public transport"*).

### Areas — `/api/v1/areas/`

| Method & path | Purpose |
|---|---|
| `GET/reviews areas/` | Neighborhood list/detail — safety, quietness, amenities, transport, schools, entertainment, family-friendly & student-friendly scores (0-100), price level, nearby places, rating breakdown | area-rating.tsx |
| `GET/POST areas/{name}/reviews/` | List/add a neighborhood review | area-rating.tsx |
| `POST areas/reviews/{review_id}/helpful/` | Toggle "Helpful" vote (real per-user count, not a client-side increment) | area-rating.tsx |

### Reviews — `/api/v1/reviews/`

| Method & path | Purpose |
|---|---|
| `GET/POST properties/{property_id}/reviews/`, `DELETE .../reviews/{id}/` | Reviews on a specific listing | apartment-details.tsx |
| `GET/POST landlords/{landlord_id}/reviews/`, `DELETE .../reviews/{id}/` | Reviews on a landlord | landlord-profile.tsx |
| `POST landlords/{landlord_id}/reviews/{id}/like/` | Toggle "helpful" like on a landlord review | landlord-profile.tsx |

Posting a review a user has already left updates it in place (one review per
user per target) rather than erroring.

### Messaging — `/api/v1/messaging/`

| Method & path | Purpose |
|---|---|
| `GET conversations/` | My conversation threads, each with the other participant, last message preview, and unread count | chat.tsx |
| `POST conversations/` | Start (or resume) a thread — `{recipient_id, property_id?, message?}` | apartment-details.tsx "Contact" button |
| `GET conversations/{id}/messages/` | Full message history (marks the other side's messages read) | chat.tsx |
| `POST conversations/{id}/messages/` | Send a message — `{text}` | chat.tsx |

### Scheduling — `/api/v1/scheduling/`

| Method & path | Purpose |
|---|---|
| `POST visits/` | Book a visit — `{property_id, full_name, email, phone, visit_date, visit_time, notes?}` | schedule.tsx |
| `GET visits/mine/?status=` | Visits I booked | buyer-dashboard.tsx "Visits" tab |
| `GET visits/received/?status=` | Visit requests on my listings | seller-dashboard.tsx |
| `POST visits/{id}/confirm/` | Landlord confirms | seller-dashboard.tsx |
| `POST visits/{id}/cancel/` | Either side cancels/reschedules — optional `{landlord_note}` | buyer-dashboard.tsx / seller-dashboard.tsx |
| `POST visits/{id}/complete/` | Mark a past visit done | seller-dashboard.tsx |

A visit request's lifecycle is `pending -> confirmed|cancelled -> completed`;
confirming/cancelling triggers an email (via `apps.common.services.notifications`)
and an in-app notification to the other party.

### Subscriptions — `/api/v1/subscriptions/`

| Method & path | Purpose |
|---|---|
| `GET plans/?role=landlord\|searcher` | Pricing cards, with nested feature list (not paginated) | pricing-plans.tsx |
| `GET me/` | My current active subscription, or `null` | pricing-plans.tsx |
| `POST subscribe/` | `{plan_id}` — subscribe/upgrade | pricing-plans.tsx |
| `POST cancel/` | Cancel my active subscription | pricing-plans.tsx |

**Payments are intentionally stubbed**, per product decision: real
Stripe/Paymob integration is out of scope for this build. `subscribe/` and
`cancel/` run through `apps/subscriptions/services/payments.py`, a
`PaymentProvider` interface with one implementation today
(`StubPaymentProvider`, which always "succeeds" without moving money). The
rest of the subscribe/cancel flow — plan lookup, deactivating the prior
subscription, persisting the new one, the response shape — is fully real
and already works end-to-end; wiring a real gateway later means adding one
class and switching `get_payment_provider()`, with no changes anywhere else.

### Notifications — `/api/v1/notifications/`

| Method & path | Purpose |
|---|---|
| `GET notifications/` | My notifications, newest first (not paginated) | dashboard "Notifications" tab |
| `GET notifications/unread_count/` | Badge count | notification bell |
| `POST notifications/{id}/read/` | Mark one read | dashboard |
| `POST notifications/read_all/` | Mark all read | dashboard |

In-app notifications are created through a single helper
(`apps/notifications/services.py::notify()`), called from the other apps
whenever something notification-worthy happens: a new message, a visit
request/confirmation/cancellation, a listing approval/rejection, a new
landlord review.

---

## Design notes

- **Role-based permissions** (`apps/common/permissions.py`) are shared
  across every app: `IsLandlord`/`IsSearcher` check `request.user.role`,
  `IsOwnerOrReadOnly` covers "edit your own X", `IsAdminRole` gates
  moderation, all composed with DRF's standard `IsAuthenticated`.
- **One exception shape everywhere.** `apps/common/exceptions.py` wraps
  DRF's default exception handling so every error — validation, 403, 404,
  throttling — comes back as `{"error": {"code", "message", "details"}}`,
  never a bare DRF default or an unhandled 500 traceback.
- **One pagination shape everywhere.** `apps/common/pagination.py`
  standardizes `count`/`total_pages`/`current_page`/`page_size`/`next`/
  `previous`/`results` on every paginated list.
- **Toggle actions** (favorite, helpful-vote, review-like) all follow the
  same `get_or_create` + delete-if-exists pattern, so the frontend can fire
  the same POST regardless of current state and read the new state off the
  response.
- **Outbound email/SMS** goes through exactly one module,
  `apps/common/services/notifications.py`. In dev it uses Django's console
  email backend (prints to the terminal); wiring a real provider (SendGrid,
  Twilio, etc.) later is a change to that one file plus the relevant
  `prod.py` settings, not a hunt through every view that sends a
  notification.
- **Nested review/message routes** are wired by hand
  (`ViewSet.as_view({method: action})` dicts in each app's `urls.py`)
  instead of adding a `drf-nested-routers` dependency for two small apps.

---

## Deployment

`config/settings/prod.py` expects `DEBUG=False`, a Postgres database via
`DB_*` env vars, `DJANGO_ALLOWED_HOSTS`, and (for real outbound email)
`EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`. It also turns on the
standard Django production security headers (SSL redirect, secure cookies,
HSTS). Serve with gunicorn behind a reverse proxy, e.g.:

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn config.wsgi:application
```

Run `python manage.py collectstatic` and `python manage.py migrate` as part
of your deploy step; media uploads (avatars, listing photos, verification
documents) should be pointed at real object storage in production rather
than local disk — swap `DEFAULT_FILE_STORAGE` in `prod.py` when that's
provisioned.

### Vercel

Vercel detects the Django project from `manage.py` and uses the explicit WSGI
entrypoint in `pyproject.toml`. Add these environment variables to the backend
Vercel project:

```text
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_ALLOWED_HOSTS=<backend-domain>,<backend-project>.vercel.app
DATABASE_URL=<managed-postgres-connection-string>
FRONTEND_URL=https://<frontend-project>.vercel.app
```

Use `CORS_ALLOWED_ORIGIN_REGEXES` for additional Vercel preview URLs when
needed. After the frontend is deployed, put its exact production URL in
`FRONTEND_URL`; do not use a trailing slash.
