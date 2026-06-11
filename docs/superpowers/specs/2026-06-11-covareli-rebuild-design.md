# Covareli.ro Rebuild — Design

**Date:** 2026-06-11
**Status:** Approved by user (pending written-spec review)

## Goal

Replace the current WordPress site covareli.ro (car rental business in Baciu, Cluj) with a custom application that keeps the same public structure, adds full online booking with card payment, and provides an admin dashboard for managing the entire content (cars, locations, prices, bookings, contact messages, settings). At the end, DNS for covareli.ro moves from the WP host to the new VPS.

## Confirmed Requirements

- Full online booking with payment via **Netopia Payments** (Romanian processor; the owner's company will open a Netopia account).
- **Full payment** at booking for now; a settings section must allow switching later to advance percentage or fixed deposit (data model and checkout prepared for it, only "full" mode implemented in UI initially).
- **Availability calendar** per car: overlapping paid/confirmed bookings block dates.
- **Bilingual**: Romanian default at `/`, full English translation under `/en/...`, language toggle in the header. Car/location descriptive fields entered in both languages in the dashboard.
- **Pricing**: per-day price with duration tiers per car (e.g. 1–2 days: 250 lei/day, 3–6: 220, 7+: 190). Total = days × matching tier price + location fees.
- **Locations**: fixed pickup/drop-off locations managed in the dashboard, each with an optional delivery fee added to the total.
- **Single admin account** (no roles), seeded by script.
- **Hosting**: own VPS (e.g. Hetzner), Docker Compose.

## Architecture

```
[Browser] ──→ [Caddy reverse proxy, HTTPS via Let's Encrypt]
                 ├──→ [Next.js :3000]  public site (SSR) + /admin dashboard
                 │        │ SSR fetch + client fetch
                 │        ▼
                 └──→ [FastAPI :8000]  REST API + Netopia webhook + image serving
                          ▼
                      [MongoDB]  + Docker volume for car images
```

- Four services in `docker-compose.yml`: `caddy`, `frontend` (Next.js, TypeScript), `backend` (FastAPI, Python 3.12, Motor/Beanie for MongoDB), `mongo`.
- Caddy terminates TLS; all public traffic over HTTPS (avoids the http→301 dropped-POST-body class of bugs).
- **Images**: uploaded from the dashboard, stored on a Docker volume, resized at upload time into card and full variants (Pillow), served by the backend. No external object storage (fleet is ~10–20 cars).
- **Admin auth**: email + password → JWT in an httpOnly, Secure cookie. Passwords hashed with bcrypt. Login rate-limited.
- **i18n**: `next-intl`; static copy in `messages/ro.json` and `messages/en.json`; dynamic content (descriptions, feature lists, location names) stored as `{ro, en}` objects in MongoDB.

### Repository layout

```
covareli/
  docker-compose.yml
  Caddyfile
  backend/        FastAPI app, tests (pytest)
  frontend/       Next.js app (App Router, TypeScript, Tailwind)
  docs/superpowers/specs/
```

## Data Model (MongoDB collections)

- **cars**: brand, model, year, body type (sedan/SUV/van/hatchback/wagon), fuel, transmission, seats, doors, engine, images[] (ordered), description {ro, en}, features[] {ro, en}, price_tiers[] [{min_days, max_days|null, price_per_day}], deposit_info (informative text), active flag, slug.
- **locations**: name {ro, en}, address, fee (RON, 0 allowed), active flag, sort order.
- **bookings**: car_id, customer {name, email, phone}, pickup {datetime, location_id}, dropoff {datetime, location_id}, price_breakdown {days, tier_price, car_total, pickup_fee, dropoff_fee, total}, status, netopia_ref, admin_notes, timestamps.
  - Status flow: `pending_payment` → `paid` → `confirmed` → `completed`; `cancelled` reachable from any non-completed state.
- **contact_messages**: name, email, phone, message, created_at, read flag.
- **settings** (singleton): payment_mode (`full` now; `advance_percent` / `fixed_deposit` reserved), advance_value, site contact details (phone, email, address). Netopia credentials (signature, API key, sandbox flag) and SMTP config live in environment variables, not in the database.
- **admin_users**: email, password_hash.

### Availability rule

A car is available for [start, end) if no booking for that car overlaps with status `paid` or `confirmed`, and no `pending_payment` booking younger than 30 minutes overlaps. Expired `pending_payment` bookings release the slot automatically (checked at query time by timestamp; no cron needed).

## Public Site (mirrors current structure)

| Page | Route (RO / EN) | Content |
|---|---|---|
| Home | `/` / `/en` | Hero + quick search form (pickup/dropoff location, dates, times) → results; "Why Covareli" 4 benefits; "How it works" 3 steps; fleet description + 4 features; phone CTA; fleet gallery |
| Cars | `/masini` / `/en/cars` | Card grid (photo, name, key specs, "from X lei/day"); filters: body type, fuel, transmission, seats, price; if dates were searched, only available cars are shown |
| Car detail | `/masini/[slug]` / `/en/cars/[slug]` | Photo gallery, full specs, features, price-tier table, date-range picker with real availability, Book button |
| Checkout | `/rezervare` / `/en/booking` | Step 1: period + locations (fees shown) + customer details; Step 2: summary with price breakdown; Step 3: redirect to Netopia → success/failure page |
| About | `/despre` / `/en/about` | Company presentation |
| Contact | `/contact` / `/en/contact` | Form (saved to DB + email to admin), map, company details |

No shopping cart — booking is a direct flow. SEO: SSR pages, per-page meta + Open Graph tags, `hreflang` pairs, sitemap.xml, structured data for the local business.

### Booking & payment flow

1. Frontend POSTs the booking → backend validates availability and price server-side, creates booking `pending_payment`, initiates a Netopia (API v2) payment, returns the redirect URL.
2. Customer pays on Netopia. Confirmation comes **only via the signed IPN/webhook**, never trusted from the browser redirect. On "paid": status → `paid`, confirmation email to customer + notification email to admin (SMTP, e.g. office@covareli.ro).
3. Browser returns to a status page that polls the booking status briefly (handles IPN race).
4. Failed/abandoned payment: slot auto-releases after 30 minutes.
5. Sandbox credentials throughout development; production keys only at launch.

## Admin Dashboard (`/admin`)

Login page → sidebar layout. Sections:

- **Bookings**: list with status/date/car filters; detail view; status transitions (confirm, complete, cancel); per-car occupancy calendar view.
- **Cars**: list + create/edit/delete; all fields incl. drag & drop image upload with reordering; price tier editor; active toggle (hide from site without deleting).
- **Locations**: CRUD with RO/EN name, address, fee, active toggle, ordering.
- **Messages**: contact form inbox, read/unread toggle.
- **Settings**: payment mode (full now; advance options visible but the alternative modes ship later), site contact details, change password. Netopia/SMTP secrets configured via environment variables, not the UI.

## Error Handling

- Server-side revalidation of availability and price at booking creation (client values are never trusted).
- Netopia IPN: signature verified; unknown/duplicate notifications are idempotent (processing keyed by booking + payment ref).
- Image upload: type/size validation, safe filenames.
- API errors return structured JSON; the frontend shows localized user-facing messages.
- Daily `mongodump` to the VPS disk via cron (simple retention, e.g. 14 days).

## Testing

- **Backend (pytest, written TDD)**: availability/overlap logic incl. the 30-minute pending window, price tier calculation + location fees, IPN signature verification and idempotency, auth.
- **End-to-end before launch**: full booking flow against Netopia sandbox on the VPS staging subdomain.

## Rollout

1. Develop locally with Docker Compose.
2. Deploy to VPS under a staging subdomain (e.g. `nou.covareli.ro`), populate real cars/locations via the dashboard, run the e2e sandbox test.
3. Switch Netopia to production keys, point covareli.ro DNS to the VPS, keep the WP host until the switch is verified, then decommission it.

## Out of Scope (v1)

- Customer accounts, online payment refunds from the dashboard (handled in Netopia's own panel), multiple admin roles, seasonal pricing, blog. Advance/deposit payment modes are prepared in the data model but their checkout UI ships only when activated.
