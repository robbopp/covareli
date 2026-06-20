# Next.js Public Site — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> When building UI components, **invoke `frontend-design` skill** to ensure production-grade visual quality.

**Goal:** Build the complete bilingual (RO/EN) public-facing Next.js site for Covareli rent-a-car: home, cars list, car detail, booking checkout with confirmation, about, and contact pages.

**Architecture:** Next.js 15 App Router + TypeScript + Tailwind CSS in `frontend/`. Bilingual routing via next-intl (RO at `/`, EN at `/en/...`) with localized pathnames. SSR for SEO pages, client fetch for availability/interactivity. Backend API at `http://localhost:8000` (dev). Booking flow: select → fill details → POST `/api/bookings` → confirmation page (no payment redirect yet; Netopia comes in a later plan).

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS 3, next-intl 3.x, native fetch. No external component libraries.

---

## Files Created / Modified

**Backend (modified):**
- `backend/app/main.py` — add CORS middleware for dev

**Frontend (all new — `frontend/` directory):**
- `package.json`, `next.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.mjs`
- `middleware.ts` — next-intl locale routing
- `i18n/routing.ts` — locale config with pathnames
- `i18n/request.ts` — server-side getRequestConfig
- `messages/ro.json` — all Romanian static copy
- `messages/en.json` — all English static copy
- `lib/types.ts` — shared TypeScript types matching backend models
- `lib/api.ts` — typed fetch wrapper for all backend endpoints
- `app/[locale]/layout.tsx` — root layout (NextIntlClientProvider, HTML structure)
- `app/[locale]/page.tsx` — home page
- `app/[locale]/masini/page.tsx` — cars list
- `app/[locale]/masini/[slug]/page.tsx` — car detail
- `app/[locale]/rezervare/page.tsx` — checkout
- `app/[locale]/rezervare/confirmare/page.tsx` — confirmation
- `app/[locale]/despre/page.tsx` — about
- `app/[locale]/contact/page.tsx` — contact
- `components/Header.tsx` — nav + language switcher
- `components/Footer.tsx`
- `components/CarCard.tsx` — car grid card
- `components/CarGallery.tsx` — photo gallery with thumbnails
- `components/PriceTierTable.tsx` — pricing table
- `components/SearchForm.tsx` — hero search (locations + dates)
- `components/ContactForm.tsx` — contact form with submit
- `app/sitemap.ts` — dynamic sitemap.xml
- `app/robots.ts` — robots.txt

---

## Task 1: Backend CORS + Next.js scaffold

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/config.py`
- Create: `frontend/` (via create-next-app + next-intl)
- Create: `frontend/i18n/routing.ts`
- Create: `frontend/i18n/request.ts`
- Create: `frontend/middleware.ts`
- Create: `frontend/next.config.ts`
- Create: `frontend/.env.local`
- Create: `frontend/.env.local.example`

- [ ] **Step 1: Add CORS allowed_origins to backend config**

In `backend/app/config.py`, add one field after `backend_url`:

```python
    cors_origins: list[str] = ["http://localhost:3000"]
```

- [ ] **Step 2: Add CORS middleware to `backend/app/main.py`**

Add import and middleware — insert these lines right after `app = FastAPI(...)`:

```python
from fastapi.middleware.cors import CORSMiddleware
```

And after `app = FastAPI(title="Covareli API", lifespan=lifespan)`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
)
```

- [ ] **Step 3: Verify backend still passes all tests**

```bash
cd /home/ubuntu/work/covareli/backend && . .venv/bin/activate && pytest tests/ -q 2>&1 | tail -5
```

Expected: `86 passed`

- [ ] **Step 4: Scaffold Next.js app**

```bash
cd /home/ubuntu/work/covareli && npx create-next-app@15 frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*" --use-npm --no-turbopack --eslint
```

When prompted, accept defaults. This creates `frontend/` with Next.js 15, TypeScript, Tailwind 3, App Router.

- [ ] **Step 5: Install next-intl**

```bash
cd /home/ubuntu/work/covareli/frontend && npm install next-intl@3
```

- [ ] **Step 6: Create `frontend/i18n/routing.ts`**

```typescript
import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['ro', 'en'] as const,
  defaultLocale: 'ro',
  localePrefix: 'as-needed',
  pathnames: {
    '/': '/',
    '/masini': {
      ro: '/masini',
      en: '/cars',
    },
    '/masini/[slug]': {
      ro: '/masini/[slug]',
      en: '/cars/[slug]',
    },
    '/rezervare': {
      ro: '/rezervare',
      en: '/booking',
    },
    '/rezervare/confirmare': {
      ro: '/rezervare/confirmare',
      en: '/booking/confirmation',
    },
    '/despre': {
      ro: '/despre',
      en: '/about',
    },
    '/contact': '/contact',
  },
});

export type Locale = (typeof routing.locales)[number];
export type Pathname = keyof typeof routing.pathnames;
```

- [ ] **Step 7: Create `frontend/i18n/request.ts`**

```typescript
import { getRequestConfig } from 'next-intl/server';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !(routing.locales as readonly string[]).includes(locale)) {
    locale = routing.defaultLocale;
  }
  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
```

- [ ] **Step 8: Create `frontend/middleware.ts`**

```typescript
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
```

- [ ] **Step 9: Replace `frontend/next.config.ts`**

```typescript
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./i18n/request.ts');

const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
    ],
  },
};

export default withNextIntl(nextConfig);
```

- [ ] **Step 10: Create `frontend/.env.local`**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

- [ ] **Step 11: Create `frontend/.env.local.example`**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

- [ ] **Step 12: Remove the default Next.js boilerplate app dir**

```bash
rm -rf /home/ubuntu/work/covareli/frontend/app
mkdir -p /home/ubuntu/work/covareli/frontend/app/\[locale\]
```

- [ ] **Step 13: Create temporary `frontend/app/[locale]/page.tsx` (placeholder)**

```tsx
export default function Home() {
  return <main><h1>Covareli</h1></main>;
}
```

- [ ] **Step 14: Create temporary `frontend/app/[locale]/layout.tsx`**

```tsx
import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';
import '../globals.css';

export const metadata: Metadata = {
  title: 'Covareli Rent-a-Car',
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!(routing.locales as readonly string[]).includes(locale)) {
    notFound();
  }
  const messages = await getMessages();
  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 15: Move globals.css to app root if needed**

```bash
ls /home/ubuntu/work/covareli/frontend/app/globals.css 2>/dev/null || echo "already gone"
```

If `globals.css` is in `frontend/app/`, move it:
```bash
mv /home/ubuntu/work/covareli/frontend/app/globals.css /home/ubuntu/work/covareli/frontend/app/globals.css 2>/dev/null; true
```

The layout imports `'../globals.css'` which resolves from `app/[locale]/layout.tsx` → `app/globals.css`. Verify the file exists at `frontend/app/globals.css`.

- [ ] **Step 16: Create stub message files**

Create `frontend/messages/ro.json`:
```json
{ "site": { "name": "Covareli" } }
```

Create `frontend/messages/en.json`:
```json
{ "site": { "name": "Covareli" } }
```

- [ ] **Step 17: Verify build passes**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: `✓ Compiled successfully` or `Route (app)` table printed with no errors.

- [ ] **Step 18: Commit**

```bash
cd /home/ubuntu/work/covareli && git add backend/app/main.py backend/app/config.py frontend/ && git commit -m "feat: add CORS middleware and scaffold Next.js 15 frontend with next-intl routing"
```

---

## Task 2: TypeScript types + API client

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`

These match the FastAPI backend models exactly. The API client is used by both server components (SSR) and client components.

- [ ] **Step 1: Create `frontend/lib/types.ts`**

```typescript
export type Locale = 'ro' | 'en';

export interface LocalizedStr {
  ro: string;
  en: string;
}

export type BodyType = 'hatchback' | 'sedan' | 'suv' | 'van' | 'wagon';
export type FuelType = 'petrol' | 'diesel' | 'hybrid' | 'electric';
export type Transmission = 'manual' | 'automatic';

export interface PriceTier {
  min_days: number;
  max_days: number | null;
  price_per_day: number;
}

export interface Car {
  id: string;
  brand: string;
  model: string;
  year: number;
  body_type: BodyType;
  fuel: FuelType;
  transmission: Transmission;
  seats: number;
  doors: number;
  engine: string;
  images: string[];
  description: LocalizedStr;
  features: LocalizedStr[];
  price_tiers: PriceTier[];
  deposit_info: LocalizedStr;
  active: boolean;
  slug: string;
  price_from: number;
}

export interface Location {
  id: string;
  name: LocalizedStr;
  address: string;
  fee: number;
}

export interface BookedRange {
  start: string;
  end: string;
}

export type BookingStatus =
  | 'pending_payment'
  | 'paid'
  | 'confirmed'
  | 'completed'
  | 'cancelled';

export interface PriceBreakdown {
  days: number;
  price_per_day: number;
  car_total: number;
  pickup_fee: number;
  dropoff_fee: number;
  total: number;
}

export interface BookingCreateRequest {
  car_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  pickup_at: string;
  dropoff_at: string;
  pickup_location_id: string;
  dropoff_location_id: string;
}

export interface BookingCreateResponse {
  booking_id: string;
  price: PriceBreakdown;
}

export interface SiteInfo {
  payment_mode: 'full' | 'advance_percent' | 'fixed_deposit';
  advance_value: number;
  contact_phone: string;
  contact_email: string;
  contact_address: string;
}

export interface CarsFilter {
  body_type?: BodyType;
  fuel?: FuelType;
  transmission?: Transmission;
  seats_min?: number;
  from?: string;
  to?: string;
}

export interface ContactRequest {
  name: string;
  email: string;
  phone?: string;
  message: string;
}
```

- [ ] **Step 2: Create `frontend/lib/api.ts`**

```typescript
import type {
  BookedRange,
  BookingCreateRequest,
  BookingCreateResponse,
  Car,
  CarsFilter,
  ContactRequest,
  Location,
  SiteInfo,
} from './types';

function backendUrl(path: string): string {
  const base =
    typeof window === 'undefined'
      ? (process.env.BACKEND_URL ?? 'http://localhost:8000')
      : (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000');
  return `${base}${path}`;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(backendUrl(path), {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(res.status, body);
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function mediaUrl(filename: string): string {
  const base =
    typeof window === 'undefined'
      ? (process.env.BACKEND_URL ?? 'http://localhost:8000')
      : (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000');
  return `${base}/media/${filename}`;
}

export async function getCars(filter: CarsFilter = {}): Promise<Car[]> {
  const params = new URLSearchParams();
  if (filter.body_type) params.set('body_type', filter.body_type);
  if (filter.fuel) params.set('fuel', filter.fuel);
  if (filter.transmission) params.set('transmission', filter.transmission);
  if (filter.seats_min) params.set('seats_min', String(filter.seats_min));
  if (filter.from) params.set('from', filter.from);
  if (filter.to) params.set('to', filter.to);
  const qs = params.toString();
  return apiFetch<Car[]>(`/api/cars${qs ? `?${qs}` : ''}`);
}

export async function getCar(slug: string): Promise<Car> {
  return apiFetch<Car>(`/api/cars/${slug}`);
}

export async function getBookedRanges(slug: string): Promise<BookedRange[]> {
  return apiFetch<BookedRange[]>(`/api/cars/${slug}/booked-ranges`);
}

export async function getLocations(): Promise<Location[]> {
  return apiFetch<Location[]>('/api/locations');
}

export async function getSiteInfo(): Promise<SiteInfo> {
  return apiFetch<SiteInfo>('/api/site-info');
}

export async function createBooking(
  data: BookingCreateRequest,
): Promise<BookingCreateResponse> {
  return apiFetch<BookingCreateResponse>('/api/bookings', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function submitContact(data: ContactRequest): Promise<void> {
  await apiFetch<{ ok: boolean }>('/api/contact', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getBookingStatus(
  bookingId: string,
): Promise<{ status: string; booking_id: string }> {
  return apiFetch(`/api/bookings/${bookingId}/status`);
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /home/ubuntu/work/covareli/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no output (0 errors).

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/lib/ && git commit -m "feat: add TypeScript types and typed API client for backend"
```

---

## Task 3: i18n messages (complete Romanian + English copy)

**Files:**
- Replace: `frontend/messages/ro.json`
- Replace: `frontend/messages/en.json`

- [ ] **Step 1: Write `frontend/messages/ro.json`**

```json
{
  "site": {
    "name": "Covareli",
    "tagline": "Închirieri auto Cluj-Napoca"
  },
  "nav": {
    "home": "Acasă",
    "cars": "Mașini",
    "about": "Despre noi",
    "contact": "Contact",
    "booking": "Rezervare"
  },
  "home": {
    "hero": {
      "title": "Închiriați o mașină în Cluj-Napoca",
      "subtitle": "Flota noastră modernă vă așteaptă. Prețuri clare, fără surprize.",
      "cta": "Caută mașini disponibile"
    },
    "search": {
      "pickup_location": "Locație preluare",
      "dropoff_location": "Locație returnare",
      "pickup_date": "Data preluare",
      "dropoff_date": "Data returnare",
      "search_button": "Caută"
    },
    "benefits": {
      "title": "De ce Covareli?",
      "items": [
        { "title": "Prețuri transparente", "desc": "Fără taxe ascunse. Plătiți exact ce vedeți." },
        { "title": "Mașini îngrijite", "desc": "Flotă întreținută regulat, verificată înainte de fiecare închiriere." },
        { "title": "Preluare flexibilă", "desc": "Aeroport, centru Cluj sau la sediul nostru din Baciu." },
        { "title": "Rezervare online", "desc": "Rezervați în câteva minute, direct de pe telefon." }
      ]
    },
    "how": {
      "title": "Cum funcționează?",
      "steps": [
        { "step": "1", "title": "Alege mașina", "desc": "Filtrează după tip, combustibil sau buget și găsește mașina potrivită." },
        { "step": "2", "title": "Completează datele", "desc": "Introduceți datele personale și locațiile de preluare și returnare." },
        { "step": "3", "title": "Confirmați și mergeți", "desc": "Primiți confirmarea pe email și vă așteptăm la data aleasă." }
      ]
    },
    "cta": {
      "title": "Gata să rezervați?",
      "subtitle": "Sunați-ne sau rezervați direct online.",
      "phone_label": "Sunați acum",
      "browse_label": "Vezi toate mașinile"
    }
  },
  "cars": {
    "title": "Parcul auto",
    "subtitle": "Alegeți mașina care vi se potrivește",
    "from_price": "de la {price} lei/zi",
    "seats": "{n} locuri",
    "doors": "{n} uși",
    "transmission_manual": "Manuală",
    "transmission_automatic": "Automată",
    "fuel_petrol": "Benzină",
    "fuel_diesel": "Motorină",
    "fuel_hybrid": "Hibrid",
    "fuel_electric": "Electric",
    "body_hatchback": "Hatchback",
    "body_sedan": "Sedan",
    "body_suv": "SUV",
    "body_van": "Van",
    "body_wagon": "Break",
    "details_button": "Vezi detalii",
    "book_button": "Rezervă",
    "no_results": "Nicio mașină disponibilă pentru criteriile selectate.",
    "filters": {
      "title": "Filtrează",
      "body_type": "Tip caroserie",
      "fuel": "Combustibil",
      "transmission": "Transmisie",
      "seats_min": "Locuri min.",
      "all": "Toate",
      "reset": "Resetează filtrele"
    }
  },
  "car_detail": {
    "specs": "Specificații",
    "features": "Dotări",
    "pricing": "Prețuri",
    "pricing_days": "{min}–{max} zile",
    "pricing_days_plus": "{min}+ zile",
    "pricing_per_day": "{price} lei/zi",
    "deposit": "Garanție",
    "book_button": "Rezervă această mașină",
    "availability": "Disponibilitate",
    "booked": "Rezervat",
    "select_dates": "Selectați perioadele de mai sus pentru a rezerva"
  },
  "checkout": {
    "title": "Rezervare",
    "summary": "Sumar rezervare",
    "car": "Mașina",
    "period": "Perioadă",
    "pickup": "Preluare",
    "dropoff": "Returnare",
    "days": "{n} zile",
    "price_per_day": "{price} lei/zi",
    "location_fee": "Taxă locație",
    "total": "Total",
    "customer_title": "Datele dumneavoastră",
    "name": "Nume complet",
    "email": "Email",
    "phone": "Telefon",
    "submit": "Confirmă rezervarea",
    "submitting": "Se procesează...",
    "no_car": "Nicio mașină selectată. Reveniți la lista de mașini.",
    "error_generic": "A apărut o eroare. Vă rugăm încercați din nou."
  },
  "confirmation": {
    "title": "Rezervare înregistrată!",
    "message": "Rezervarea dvs. a fost înregistrată cu succes. Vă vom contacta în cel mai scurt timp pentru confirmare.",
    "booking_id": "ID rezervare: {id}",
    "back_home": "Înapoi acasă",
    "contact_us": "Sunați-ne la {phone}"
  },
  "about": {
    "title": "Despre noi",
    "p1": "Covareli este o firmă de închirieri auto cu sediul în Baciu, Cluj-Napoca. Oferim servicii de calitate cu o flotă modernă și îngrijită.",
    "p2": "Ne mândrim cu transparența prețurilor, flexibilitatea în preluare și returnare și cu relația personală cu fiecare client.",
    "p3": "Fie că aveți nevoie de o mașină pentru o zi sau pentru mai mult timp, suntem aici să vă ajutăm.",
    "contact_title": "Date de contact",
    "address": "Str. Jupiter, nr. 1/12, Baciu, Cluj",
    "phone": "+40 749 323 172",
    "email": "office@covareli.ro"
  },
  "contact": {
    "title": "Contact",
    "subtitle": "Scrieți-ne sau sunați-ne",
    "form_title": "Trimite un mesaj",
    "name": "Nume",
    "email": "Email",
    "phone": "Telefon (opțional)",
    "message": "Mesaj",
    "send": "Trimite",
    "sending": "Se trimite...",
    "success": "Mesajul a fost trimis! Vă vom răspunde în scurt timp.",
    "error": "A apărut o eroare. Vă rugăm încercați din nou.",
    "info_title": "Date de contact",
    "address": "Str. Jupiter, nr. 1/12, Baciu, Cluj",
    "phone_val": "+40 749 323 172",
    "email_val": "office@covareli.ro",
    "hours": "Luni–Vineri: 08:00–18:00 | Sâmbătă: 09:00–14:00"
  },
  "footer": {
    "rights": "© {year} Covareli. Toate drepturile rezervate.",
    "links_title": "Pagini",
    "contact_title": "Contact"
  },
  "errors": {
    "not_found": "Pagina nu a fost găsită",
    "back_home": "Înapoi acasă"
  }
}
```

- [ ] **Step 2: Write `frontend/messages/en.json`**

```json
{
  "site": {
    "name": "Covareli",
    "tagline": "Car Rentals Cluj-Napoca"
  },
  "nav": {
    "home": "Home",
    "cars": "Cars",
    "about": "About",
    "contact": "Contact",
    "booking": "Booking"
  },
  "home": {
    "hero": {
      "title": "Rent a Car in Cluj-Napoca",
      "subtitle": "Our modern fleet is ready for you. Clear prices, no surprises.",
      "cta": "Find available cars"
    },
    "search": {
      "pickup_location": "Pickup location",
      "dropoff_location": "Drop-off location",
      "pickup_date": "Pickup date",
      "dropoff_date": "Drop-off date",
      "search_button": "Search"
    },
    "benefits": {
      "title": "Why Covareli?",
      "items": [
        { "title": "Transparent pricing", "desc": "No hidden fees. You pay exactly what you see." },
        { "title": "Well-maintained cars", "desc": "Fleet regularly serviced and checked before every rental." },
        { "title": "Flexible pickup", "desc": "Airport, Cluj city centre, or our office in Baciu." },
        { "title": "Online booking", "desc": "Reserve in minutes, straight from your phone." }
      ]
    },
    "how": {
      "title": "How does it work?",
      "steps": [
        { "step": "1", "title": "Choose a car", "desc": "Filter by type, fuel, or budget and find the right car." },
        { "step": "2", "title": "Enter your details", "desc": "Fill in your personal information and pickup/drop-off locations." },
        { "step": "3", "title": "Confirm and go", "desc": "Receive email confirmation and we'll be waiting at the agreed date." }
      ]
    },
    "cta": {
      "title": "Ready to book?",
      "subtitle": "Call us or book directly online.",
      "phone_label": "Call now",
      "browse_label": "Browse all cars"
    }
  },
  "cars": {
    "title": "Our fleet",
    "subtitle": "Choose the car that suits you",
    "from_price": "from {price} RON/day",
    "seats": "{n} seats",
    "doors": "{n} doors",
    "transmission_manual": "Manual",
    "transmission_automatic": "Automatic",
    "fuel_petrol": "Petrol",
    "fuel_diesel": "Diesel",
    "fuel_hybrid": "Hybrid",
    "fuel_electric": "Electric",
    "body_hatchback": "Hatchback",
    "body_sedan": "Sedan",
    "body_suv": "SUV",
    "body_van": "Van",
    "body_wagon": "Estate",
    "details_button": "View details",
    "book_button": "Book",
    "no_results": "No cars available for the selected criteria.",
    "filters": {
      "title": "Filter",
      "body_type": "Body type",
      "fuel": "Fuel",
      "transmission": "Transmission",
      "seats_min": "Min. seats",
      "all": "All",
      "reset": "Reset filters"
    }
  },
  "car_detail": {
    "specs": "Specifications",
    "features": "Features",
    "pricing": "Pricing",
    "pricing_days": "{min}–{max} days",
    "pricing_days_plus": "{min}+ days",
    "pricing_per_day": "{price} RON/day",
    "deposit": "Deposit",
    "book_button": "Book this car",
    "availability": "Availability",
    "booked": "Booked",
    "select_dates": "Select dates above to proceed with booking"
  },
  "checkout": {
    "title": "Booking",
    "summary": "Booking summary",
    "car": "Car",
    "period": "Period",
    "pickup": "Pickup",
    "dropoff": "Drop-off",
    "days": "{n} days",
    "price_per_day": "{price} RON/day",
    "location_fee": "Location fee",
    "total": "Total",
    "customer_title": "Your details",
    "name": "Full name",
    "email": "Email",
    "phone": "Phone",
    "submit": "Confirm booking",
    "submitting": "Processing...",
    "no_car": "No car selected. Return to the car list.",
    "error_generic": "Something went wrong. Please try again."
  },
  "confirmation": {
    "title": "Booking received!",
    "message": "Your booking has been successfully registered. We will contact you shortly to confirm.",
    "booking_id": "Booking ID: {id}",
    "back_home": "Back to home",
    "contact_us": "Call us at {phone}"
  },
  "about": {
    "title": "About us",
    "p1": "Covareli is a car rental company based in Baciu, Cluj-Napoca. We offer quality service with a modern, well-maintained fleet.",
    "p2": "We pride ourselves on transparent pricing, flexible pickup and drop-off, and a personal relationship with every customer.",
    "p3": "Whether you need a car for a day or longer, we are here to help.",
    "contact_title": "Contact details",
    "address": "Str. Jupiter, nr. 1/12, Baciu, Cluj",
    "phone": "+40 749 323 172",
    "email": "office@covareli.ro"
  },
  "contact": {
    "title": "Contact",
    "subtitle": "Write to us or give us a call",
    "form_title": "Send a message",
    "name": "Name",
    "email": "Email",
    "phone": "Phone (optional)",
    "message": "Message",
    "send": "Send",
    "sending": "Sending...",
    "success": "Message sent! We will get back to you shortly.",
    "error": "Something went wrong. Please try again.",
    "info_title": "Contact details",
    "address": "Str. Jupiter, nr. 1/12, Baciu, Cluj",
    "phone_val": "+40 749 323 172",
    "email_val": "office@covareli.ro",
    "hours": "Mon–Fri: 08:00–18:00 | Sat: 09:00–14:00"
  },
  "footer": {
    "rights": "© {year} Covareli. All rights reserved.",
    "links_title": "Pages",
    "contact_title": "Contact"
  },
  "errors": {
    "not_found": "Page not found",
    "back_home": "Back to home"
  }
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /home/ubuntu/work/covareli/frontend && npx tsc --noEmit 2>&1 | head -10
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/messages/ && git commit -m "feat: add complete Romanian and English i18n messages"
```

---

## Task 4: Layout — Header, Footer, root layout

**Files:**
- Create: `frontend/components/Header.tsx`
- Create: `frontend/components/Footer.tsx`
- Replace: `frontend/app/[locale]/layout.tsx`

> **Use `frontend-design` skill** for visual quality on this task.

- [ ] **Step 1: Create `frontend/components/Header.tsx`**

```tsx
'use client';

import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';

export default function Header() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  const otherLocale = locale === 'ro' ? 'en' : 'ro';

  function switchLocale() {
    // Strip current locale prefix and add the other
    const withoutLocale = pathname.replace(/^\/(en)(\/|$)/, '/');
    if (otherLocale === 'en') {
      router.push(`/en${withoutLocale === '/' ? '' : withoutLocale}`);
    } else {
      router.push(withoutLocale || '/');
    }
  }

  const navLinks = [
    { href: locale === 'ro' ? '/masini' : '/en/cars', label: t('cars') },
    { href: locale === 'ro' ? '/despre' : '/en/about', label: t('about') },
    { href: '/contact', label: t('contact') },
  ];

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16">
        <Link href={locale === 'ro' ? '/' : '/en'} className="text-xl font-bold text-blue-700 tracking-tight">
          Covareli
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-gray-600 hover:text-blue-700 font-medium transition-colors"
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={switchLocale}
            className="ml-4 px-3 py-1 border border-gray-300 rounded text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            {otherLocale.toUpperCase()}
          </button>
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-gray-600"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          <span className="block w-6 h-0.5 bg-current mb-1" />
          <span className="block w-6 h-0.5 bg-current mb-1" />
          <span className="block w-6 h-0.5 bg-current" />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white px-4 py-3 flex flex-col gap-3">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-gray-700 font-medium py-1"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={() => { switchLocale(); setMenuOpen(false); }}
            className="self-start px-3 py-1 border border-gray-300 rounded text-sm font-medium"
          >
            {otherLocale.toUpperCase()}
          </button>
        </div>
      )}
    </header>
  );
}
```

- [ ] **Step 2: Create `frontend/components/Footer.tsx`**

```tsx
import { useTranslations } from 'next-intl';

export default function Footer() {
  const t = useTranslations('footer');
  const year = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-gray-400 mt-auto">
      <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <p className="text-white font-bold text-lg mb-2">Covareli</p>
          <p className="text-sm">Str. Jupiter, nr. 1/12, Baciu, Cluj</p>
          <p className="text-sm">+40 749 323 172</p>
          <p className="text-sm">office@covareli.ro</p>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">{t('links_title')}</p>
          <ul className="space-y-1 text-sm">
            <li><a href="/" className="hover:text-white transition-colors">Acasă</a></li>
            <li><a href="/masini" className="hover:text-white transition-colors">Mașini</a></li>
            <li><a href="/despre" className="hover:text-white transition-colors">Despre noi</a></li>
            <li><a href="/contact" className="hover:text-white transition-colors">Contact</a></li>
          </ul>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">{t('contact_title')}</p>
          <p className="text-sm">Luni–Vineri: 08:00–18:00</p>
          <p className="text-sm">Sâmbătă: 09:00–14:00</p>
        </div>
      </div>
      <div className="border-t border-gray-800 text-center text-xs py-4 text-gray-600">
        {t('rights', { year })}
      </div>
    </footer>
  );
}
```

- [ ] **Step 3: Replace `frontend/app/[locale]/layout.tsx`**

```tsx
import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import '../globals.css';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'site' });
  return {
    title: { default: t('name'), template: `%s | ${t('name')}` },
    description: t('tagline'),
  };
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!(routing.locales as readonly string[]).includes(locale)) {
    notFound();
  }
  const messages = await getMessages();
  return (
    <html lang={locale}>
      <body className="flex flex-col min-h-screen bg-gray-50 text-gray-900 antialiased">
        <NextIntlClientProvider messages={messages}>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 4: Verify build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: build succeeds (no TypeScript errors, no missing modules).

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/components/Header.tsx frontend/components/Footer.tsx frontend/app/\[locale\]/layout.tsx && git commit -m "feat: add bilingual Header and Footer with mobile menu and locale switcher"
```

---

## Task 5: Home page

**Files:**
- Replace: `frontend/app/[locale]/page.tsx`
- Create: `frontend/components/SearchForm.tsx`

> **Use `frontend-design` skill** for visual quality on this task.

- [ ] **Step 1: Create `frontend/components/SearchForm.tsx`**

A client component: lets users pick pickup/dropoff location + dates, then navigates to the cars page with params.

```tsx
'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { getLocations } from '@/lib/api';
import type { Location } from '@/lib/types';

export default function SearchForm() {
  const t = useTranslations('home.search');
  const locale = useLocale();
  const router = useRouter();
  const [locations, setLocations] = useState<Location[]>([]);
  const [pickupId, setPickupId] = useState('');
  const [dropoffId, setDropoffId] = useState('');
  const [pickupDate, setPickupDate] = useState('');
  const [dropoffDate, setDropoffDate] = useState('');

  useEffect(() => {
    getLocations().then(setLocations).catch(() => {});
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const carsPath = locale === 'ro' ? '/masini' : '/en/cars';
    const params = new URLSearchParams();
    if (pickupId) params.set('pickup', pickupId);
    if (dropoffId) params.set('dropoff', dropoffId);
    if (pickupDate) params.set('from', `${pickupDate}T10:00:00`);
    if (dropoffDate) params.set('to', `${dropoffDate}T10:00:00`);
    router.push(`${carsPath}?${params.toString()}`);
  }

  const today = new Date().toISOString().split('T')[0];

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('pickup_location')}</label>
        <select
          value={pickupId}
          onChange={(e) => setPickupId(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">—</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>{locale === 'ro' ? l.name.ro : l.name.en}</option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('dropoff_location')}</label>
        <select
          value={dropoffId}
          onChange={(e) => setDropoffId(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">—</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>{locale === 'ro' ? l.name.ro : l.name.en}</option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('pickup_date')}</label>
        <input
          type="date"
          min={today}
          value={pickupDate}
          onChange={(e) => setPickupDate(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('dropoff_date')}</label>
        <input
          type="date"
          min={pickupDate || today}
          value={dropoffDate}
          onChange={(e) => setDropoffDate(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="sm:col-span-2 lg:col-span-4">
        <button
          type="submit"
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
        >
          {t('search_button')}
        </button>
      </div>
    </form>
  );
}
```

- [ ] **Step 2: Replace `frontend/app/[locale]/page.tsx`**

```tsx
import { getTranslations } from 'next-intl/server';
import Link from 'next/link';
import SearchForm from '@/components/SearchForm';
import type { Metadata } from 'next';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'home.hero' });
  return { title: t('title') };
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale });

  const benefits: { title: string; desc: string }[] = t.raw('home.benefits.items');
  const steps: { step: string; title: string; desc: string }[] = t.raw('home.how.steps');

  const carsPath = locale === 'ro' ? '/masini' : '/en/cars';

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-700 to-blue-900 text-white">
        <div className="max-w-6xl mx-auto px-4 py-20">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 max-w-2xl leading-tight">
            {t('home.hero.title')}
          </h1>
          <p className="text-blue-100 text-lg mb-10 max-w-xl">
            {t('home.hero.subtitle')}
          </p>
          <SearchForm />
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">{t('home.benefits.title')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((b, i) => (
              <div key={i} className="text-center p-6 rounded-2xl bg-gray-50 hover:shadow-md transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-blue-700 font-bold text-lg">{i + 1}</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{b.title}</h3>
                <p className="text-sm text-gray-500">{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">{t('home.how.title')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {steps.map((s, i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-full bg-blue-700 text-white flex items-center justify-center text-2xl font-bold mb-4">
                  {s.step}
                </div>
                <h3 className="font-semibold text-lg mb-2">{s.title}</h3>
                <p className="text-gray-500 text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-blue-700 text-white text-center">
        <div className="max-w-2xl mx-auto px-4">
          <h2 className="text-3xl font-bold mb-3">{t('home.cta.title')}</h2>
          <p className="text-blue-100 mb-8">{t('home.cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="tel:+40749323172"
              className="bg-white text-blue-700 font-semibold px-8 py-3 rounded-xl hover:bg-blue-50 transition-colors"
            >
              {t('home.cta.phone_label')}
            </a>
            <Link
              href={carsPath}
              className="border-2 border-white text-white font-semibold px-8 py-3 rounded-xl hover:bg-blue-800 transition-colors"
            >
              {t('home.cta.browse_label')}
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/app/\[locale\]/page.tsx frontend/components/SearchForm.tsx && git commit -m "feat: add home page with hero search form, benefits, and how-it-works sections"
```

---

## Task 6: Cars list page

**Files:**
- Create: `frontend/app/[locale]/masini/page.tsx`
- Create: `frontend/components/CarCard.tsx`

> **Use `frontend-design` skill** for visual quality on this task.

The cars page is an SSR page that fetches the full list server-side. If the URL has `from`/`to` params, it also passes them to the API to filter by availability. Client-side filters (body_type, fuel, transmission, seats_min) are applied in the browser without re-fetching.

- [ ] **Step 1: Create `frontend/components/CarCard.tsx`**

```tsx
import Link from 'next/link';
import Image from 'next/image';
import { useLocale, useTranslations } from 'next-intl';
import { mediaUrl } from '@/lib/api';
import type { Car } from '@/lib/types';

interface Props {
  car: Car;
}

export default function CarCard({ car }: Props) {
  const t = useTranslations('cars');
  const locale = useLocale();
  const detailPath = locale === 'ro' ? `/masini/${car.slug}` : `/en/cars/${car.slug}`;
  const thumb = car.images[0] ? mediaUrl(car.images[0].replace('.webp', '-card.webp')) : null;

  const fuelKey = `fuel_${car.fuel}` as const;
  const transKey = `transmission_${car.transmission}` as const;

  return (
    <div className="bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col">
      <div className="aspect-video bg-gray-100 relative">
        {thumb ? (
          <Image src={thumb} alt={`${car.brand} ${car.model}`} fill className="object-cover" sizes="(max-width: 768px) 100vw, 33vw" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-4xl">🚗</div>
        )}
      </div>
      <div className="p-5 flex flex-col flex-1">
        <h3 className="font-bold text-lg text-gray-900">{car.brand} {car.model} <span className="text-gray-400 font-normal text-base">{car.year}</span></h3>
        <div className="flex flex-wrap gap-2 mt-2 mb-4">
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{t(fuelKey)}</span>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{t(transKey)}</span>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{t('seats', { n: car.seats })}</span>
        </div>
        <p className="text-blue-700 font-semibold mt-auto mb-4">{t('from_price', { price: car.price_from })}</p>
        <Link
          href={detailPath}
          className="block text-center bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2.5 rounded-xl transition-colors text-sm"
        >
          {t('details_button')}
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/app/[locale]/masini/page.tsx`**

```tsx
import { getTranslations } from 'next-intl/server';
import type { Metadata } from 'next';
import { getCars } from '@/lib/api';
import type { BodyType, Car, FuelType, Transmission } from '@/lib/types';
import CarsClientPage from './CarsClientPage';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'cars' });
  return { title: t('title') };
}

export default async function CarsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ from?: string; to?: string; pickup?: string; dropoff?: string }>;
}) {
  const { locale } = await params;
  const sp = await searchParams;

  const cars = await getCars({
    from: sp.from,
    to: sp.to,
  }).catch(() => [] as Car[]);

  return <CarsClientPage initialCars={cars} locale={locale} />;
}
```

- [ ] **Step 3: Create `frontend/app/[locale]/masini/CarsClientPage.tsx`**

This is a client component that handles the in-browser filters.

```tsx
'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import CarCard from '@/components/CarCard';
import type { BodyType, Car, FuelType, Transmission } from '@/lib/types';

interface Props {
  initialCars: Car[];
  locale: string;
}

const BODY_TYPES: BodyType[] = ['hatchback', 'sedan', 'suv', 'van', 'wagon'];
const FUEL_TYPES: FuelType[] = ['petrol', 'diesel', 'hybrid', 'electric'];
const TRANSMISSIONS: Transmission[] = ['manual', 'automatic'];

export default function CarsClientPage({ initialCars, locale }: Props) {
  const t = useTranslations('cars');
  const [bodyType, setBodyType] = useState<BodyType | ''>('');
  const [fuel, setFuel] = useState<FuelType | ''>('');
  const [transmission, setTransmission] = useState<Transmission | ''>('');
  const [seatsMin, setSeatsMin] = useState('');

  const filtered = initialCars.filter((car) => {
    if (bodyType && car.body_type !== bodyType) return false;
    if (fuel && car.fuel !== fuel) return false;
    if (transmission && car.transmission !== transmission) return false;
    if (seatsMin && car.seats < parseInt(seatsMin)) return false;
    return true;
  });

  function reset() {
    setBodyType('');
    setFuel('');
    setTransmission('');
    setSeatsMin('');
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-2">{t('title')}</h1>
      <p className="text-gray-500 mb-8">{t('subtitle')}</p>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Filters sidebar */}
        <aside className="lg:w-56 shrink-0">
          <div className="bg-white rounded-2xl shadow-sm p-5 sticky top-20">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">{t('filters.title')}</h2>
              <button onClick={reset} className="text-xs text-blue-700 hover:underline">{t('filters.reset')}</button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('filters.body_type')}</label>
                <select value={bodyType} onChange={(e) => setBodyType(e.target.value as BodyType | '')} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">{t('filters.all')}</option>
                  {BODY_TYPES.map((bt) => <option key={bt} value={bt}>{t(`body_${bt}` as any)}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('filters.fuel')}</label>
                <select value={fuel} onChange={(e) => setFuel(e.target.value as FuelType | '')} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">{t('filters.all')}</option>
                  {FUEL_TYPES.map((f) => <option key={f} value={f}>{t(`fuel_${f}` as any)}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('filters.transmission')}</label>
                <select value={transmission} onChange={(e) => setTransmission(e.target.value as Transmission | '')} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">{t('filters.all')}</option>
                  {TRANSMISSIONS.map((tr) => <option key={tr} value={tr}>{t(`transmission_${tr}` as any)}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('filters.seats_min')}</label>
                <input type="number" min="2" max="9" value={seatsMin} onChange={(e) => setSeatsMin(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="2" />
              </div>
            </div>
          </div>
        </aside>

        {/* Car grid */}
        <div className="flex-1">
          {filtered.length === 0 ? (
            <p className="text-gray-500 py-12 text-center">{t('no_results')}</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {filtered.map((car) => <CarCard key={car.id} car={car} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/app/\[locale\]/masini/ frontend/components/CarCard.tsx && git commit -m "feat: add cars list page with SSR + client-side filters"
```

---

## Task 7: Car detail page

**Files:**
- Create: `frontend/app/[locale]/masini/[slug]/page.tsx`
- Create: `frontend/components/CarGallery.tsx`
- Create: `frontend/components/PriceTierTable.tsx`

> **Use `frontend-design` skill** for visual quality on this task.

The car detail page: SSR fetches car data, renders specs, gallery, pricing. A "Rezervă" button links to the checkout page with query params (car slug, selected dates).

- [ ] **Step 1: Create `frontend/components/CarGallery.tsx`**

```tsx
'use client';

import Image from 'next/image';
import { useState } from 'react';
import { mediaUrl } from '@/lib/api';

interface Props {
  images: string[];
  alt: string;
}

export default function CarGallery({ images, alt }: Props) {
  const [active, setActive] = useState(0);

  if (images.length === 0) {
    return (
      <div className="aspect-video bg-gray-100 rounded-2xl flex items-center justify-center text-gray-300 text-6xl">🚗</div>
    );
  }

  return (
    <div>
      <div className="aspect-video relative rounded-2xl overflow-hidden bg-gray-100 mb-3">
        <Image
          src={mediaUrl(images[active])}
          alt={alt}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 55vw"
          priority
        />
      </div>
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((img, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
              className={`relative w-20 h-14 rounded-lg overflow-hidden shrink-0 border-2 transition-colors ${i === active ? 'border-blue-700' : 'border-transparent'}`}
            >
              <Image src={mediaUrl(img.replace('.webp', '-card.webp'))} alt="" fill className="object-cover" sizes="80px" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/components/PriceTierTable.tsx`**

```tsx
import { useTranslations } from 'next-intl';
import type { PriceTier } from '@/lib/types';

interface Props {
  tiers: PriceTier[];
}

export default function PriceTierTable({ tiers }: Props) {
  const t = useTranslations('car_detail');
  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="bg-gray-50">
          <th className="text-left px-4 py-2 font-semibold text-gray-600 rounded-tl-lg">{t('pricing')}</th>
          <th className="text-right px-4 py-2 font-semibold text-gray-600 rounded-tr-lg">Lei/zi</th>
        </tr>
      </thead>
      <tbody>
        {tiers.map((tier, i) => (
          <tr key={i} className="border-t border-gray-100">
            <td className="px-4 py-2 text-gray-700">
              {tier.max_days
                ? t('pricing_days', { min: tier.min_days, max: tier.max_days })
                : t('pricing_days_plus', { min: tier.min_days })}
            </td>
            <td className="px-4 py-2 text-right font-semibold text-blue-700">
              {tier.price_per_day}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 3: Create `frontend/app/[locale]/masini/[slug]/page.tsx`**

```tsx
import { getTranslations } from 'next-intl/server';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ApiError, getCar } from '@/lib/api';
import CarGallery from '@/components/CarGallery';
import PriceTierTable from '@/components/PriceTierTable';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  try {
    const car = await getCar(slug);
    return { title: `${car.brand} ${car.model} ${car.year}` };
  } catch {
    return { title: 'Mașină' };
  }
}

export default async function CarDetailPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  const t = await getTranslations({ locale });

  let car;
  try {
    car = await getCar(slug);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  const desc = locale === 'ro' ? car.description.ro : car.description.en;
  const features = car.features.map((f) => (locale === 'ro' ? f.ro : f.en));
  const depositText = locale === 'ro' ? car.deposit_info.ro : car.deposit_info.en;

  const checkoutPath = locale === 'ro' ? '/rezervare' : '/en/booking';
  const bookUrl = `${checkoutPath}?car=${car.slug}`;

  const fuelLabel = t(`cars.fuel_${car.fuel}` as any);
  const transLabel = t(`cars.transmission_${car.transmission}` as any);
  const bodyLabel = t(`cars.body_${car.body_type}` as any);

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Left: gallery */}
        <div>
          <CarGallery images={car.images} alt={`${car.brand} ${car.model}`} />
        </div>

        {/* Right: info */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">
            {car.brand} {car.model}
          </h1>
          <p className="text-gray-500 mb-6">{car.year}</p>

          {desc && <p className="text-gray-600 mb-6 leading-relaxed">{desc}</p>}

          {/* Specs */}
          <h2 className="font-semibold text-gray-900 mb-3">{t('car_detail.specs')}</h2>
          <div className="grid grid-cols-2 gap-2 mb-6">
            {[
              ['Tip', bodyLabel],
              ['Combustibil', fuelLabel],
              ['Transmisie', transLabel],
              ['Locuri', String(car.seats)],
              ['Uși', String(car.doors)],
              car.engine ? ['Motor', car.engine] : null,
            ].filter(Boolean).map(([label, value]) => (
              <div key={label} className="bg-gray-50 rounded-lg px-3 py-2">
                <p className="text-xs text-gray-400">{label}</p>
                <p className="font-medium text-gray-800 text-sm">{value}</p>
              </div>
            ))}
          </div>

          {/* Features */}
          {features.filter(Boolean).length > 0 && (
            <>
              <h2 className="font-semibold text-gray-900 mb-3">{t('car_detail.features')}</h2>
              <ul className="grid grid-cols-2 gap-1 mb-6">
                {features.filter(Boolean).map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                    <span className="text-blue-600">✓</span> {f}
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Pricing */}
          <h2 className="font-semibold text-gray-900 mb-3">{t('car_detail.pricing')}</h2>
          <div className="rounded-xl overflow-hidden border border-gray-100 mb-4">
            <PriceTierTable tiers={car.price_tiers} />
          </div>

          {depositText && (
            <p className="text-sm text-gray-500 mb-6">
              <span className="font-semibold">{t('car_detail.deposit')}:</span> {depositText}
            </p>
          )}

          <Link
            href={bookUrl}
            className="block text-center bg-blue-700 hover:bg-blue-800 text-white font-semibold py-4 rounded-xl transition-colors text-base"
          >
            {t('car_detail.book_button')}
          </Link>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/app/\[locale\]/masini/\[slug\]/ frontend/components/CarGallery.tsx frontend/components/PriceTierTable.tsx && git commit -m "feat: add car detail page with gallery, specs, features, and pricing table"
```

---

## Task 8: Checkout + Confirmation

**Files:**
- Create: `frontend/app/[locale]/rezervare/page.tsx`
- Create: `frontend/app/[locale]/rezervare/confirmare/page.tsx`

> **Use `frontend-design` skill** for visual quality on this task.

Flow: URL params `?car=slug&from=...&to=...&pickup=loc_id&dropoff=loc_id`. Page fetches car + locations, shows summary + form. On submit: POST `/api/bookings` → redirect to `/rezervare/confirmare?booking=id`.

- [ ] **Step 1: Create `frontend/app/[locale]/rezervare/page.tsx`**

```tsx
'use client';

import { useEffect, useState } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { createBooking, getCar, getLocations } from '@/lib/api';
import type { Car, Location, PriceBreakdown } from '@/lib/types';

function CheckoutContent() {
  const t = useTranslations('checkout');
  const locale = useLocale();
  const router = useRouter();
  const sp = useSearchParams();

  const carSlug = sp.get('car') ?? '';
  const fromStr = sp.get('from') ?? '';
  const toStr = sp.get('to') ?? '';
  const pickupId = sp.get('pickup') ?? '';
  const dropoffId = sp.get('dropoff') ?? '';

  const [car, setCar] = useState<Car | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedPickup, setSelectedPickup] = useState(pickupId);
  const [selectedDropoff, setSelectedDropoff] = useState(dropoffId);
  const [pickupDate, setPickupDate] = useState(fromStr ? fromStr.split('T')[0] : '');
  const [dropoffDate, setDropoffDate] = useState(toStr ? toStr.split('T')[0] : '');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (carSlug) getCar(carSlug).then(setCar).catch(() => {});
    getLocations().then(setLocations).catch(() => {});
  }, [carSlug]);

  const pickupLoc = locations.find((l) => l.id === selectedPickup);
  const dropoffLoc = locations.find((l) => l.id === selectedDropoff);

  function calcDays(): number {
    if (!pickupDate || !dropoffDate) return 0;
    const diff = new Date(dropoffDate).getTime() - new Date(pickupDate).getTime();
    return Math.max(1, Math.ceil(diff / 86400000));
  }

  function matchingTierPrice(): number {
    if (!car) return 0;
    const days = calcDays();
    const tier = car.price_tiers.find(
      (t) => days >= t.min_days && (t.max_days === null || days <= t.max_days),
    );
    return tier?.price_per_day ?? 0;
  }

  const days = calcDays();
  const ppd = matchingTierPrice();
  const carTotal = days * ppd;
  const pickupFee = pickupLoc?.fee ?? 0;
  const dropoffFee = dropoffLoc?.fee ?? 0;
  const total = carTotal + pickupFee + dropoffFee;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!car || !selectedPickup || !selectedDropoff || !pickupDate || !dropoffDate) {
      setError(t('error_generic'));
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const result = await createBooking({
        car_id: car.id,
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
        pickup_at: `${pickupDate}T10:00:00`,
        dropoff_at: `${dropoffDate}T10:00:00`,
        pickup_location_id: selectedPickup,
        dropoff_location_id: selectedDropoff,
      });
      const confirmPath = locale === 'ro' ? '/rezervare/confirmare' : '/en/booking/confirmation';
      router.push(`${confirmPath}?booking=${result.booking_id}`);
    } catch {
      setError(t('error_generic'));
      setSubmitting(false);
    }
  }

  if (!carSlug) {
    return <div className="max-w-2xl mx-auto px-4 py-20 text-center text-gray-500">{t('no_car')}</div>;
  }

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-8">{t('title')}</h1>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Form */}
        <form onSubmit={handleSubmit} className="lg:col-span-3 space-y-6">
          {/* Period */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-4">{t('period')}</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('pickup')}</label>
                <input type="date" required min={today} value={pickupDate} onChange={(e) => setPickupDate(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('dropoff')}</label>
                <input type="date" required min={pickupDate || today} value={dropoffDate} onChange={(e) => setDropoffDate(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
          </div>

          {/* Locations */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Locații</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('pickup')}</label>
                <select required value={selectedPickup} onChange={(e) => setSelectedPickup(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">—</option>
                  {locations.map((l) => <option key={l.id} value={l.id}>{locale === 'ro' ? l.name.ro : l.name.en}{l.fee > 0 ? ` (+${l.fee} lei)` : ''}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('dropoff')}</label>
                <select required value={selectedDropoff} onChange={(e) => setSelectedDropoff(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">—</option>
                  {locations.map((l) => <option key={l.id} value={l.id}>{locale === 'ro' ? l.name.ro : l.name.en}{l.fee > 0 ? ` (+${l.fee} lei)` : ''}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Customer */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-4">{t('customer_title')}</h2>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('name')}</label>
                <input required minLength={2} value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('email')}</label>
                <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="text-xs text-gray-500 font-semibold uppercase tracking-wide block mb-1">{t('phone')}</label>
                <input required minLength={4} value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-50 text-white font-semibold py-4 rounded-xl transition-colors text-base"
          >
            {submitting ? t('submitting') : t('submit')}
          </button>
        </form>

        {/* Summary */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-sm p-6 sticky top-20">
            <h2 className="font-semibold text-gray-900 mb-4">{t('summary')}</h2>
            {car && (
              <>
                <p className="font-bold text-gray-900 mb-1">{car.brand} {car.model} {car.year}</p>
                {days > 0 && ppd > 0 && (
                  <div className="space-y-2 mt-4 text-sm">
                    <div className="flex justify-between text-gray-600">
                      <span>{t('days', { n: days })} × {ppd} lei</span>
                      <span>{carTotal} lei</span>
                    </div>
                    {pickupFee > 0 && (
                      <div className="flex justify-between text-gray-600">
                        <span>{t('location_fee')} ({t('pickup')})</span>
                        <span>{pickupFee} lei</span>
                      </div>
                    )}
                    {dropoffFee > 0 && (
                      <div className="flex justify-between text-gray-600">
                        <span>{t('location_fee')} ({t('dropoff')})</span>
                        <span>{dropoffFee} lei</span>
                      </div>
                    )}
                    <div className="border-t border-gray-100 pt-2 flex justify-between font-bold text-gray-900">
                      <span>{t('total')}</span>
                      <span className="text-blue-700">{total} lei</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense>
      <CheckoutContent />
    </Suspense>
  );
}
```

- [ ] **Step 2: Create `frontend/app/[locale]/rezervare/confirmare/page.tsx`**

```tsx
'use client';

import { Suspense } from 'react';
import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

function ConfirmationContent() {
  const t = useTranslations('confirmation');
  const sp = useSearchParams();
  const bookingId = sp.get('booking') ?? '';

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-4xl">✓</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">{t('title')}</h1>
        <p className="text-gray-600 mb-4 leading-relaxed">{t('message')}</p>
        {bookingId && (
          <p className="text-sm text-gray-400 mb-6 font-mono">{t('booking_id', { id: bookingId.slice(0, 8) })}</p>
        )}
        <p className="text-blue-700 font-semibold mb-8">
          {t('contact_us', { phone: '+40 749 323 172' })}
        </p>
        <Link
          href="/"
          className="inline-block bg-blue-700 hover:bg-blue-800 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
        >
          {t('back_home')}
        </Link>
      </div>
    </div>
  );
}

export default function ConfirmationPage() {
  return (
    <Suspense>
      <ConfirmationContent />
    </Suspense>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/app/\[locale\]/rezervare/ && git commit -m "feat: add checkout page with booking form and confirmation page"
```

---

## Task 9: About + Contact pages

**Files:**
- Create: `frontend/app/[locale]/despre/page.tsx`
- Create: `frontend/app/[locale]/contact/page.tsx`
- Create: `frontend/components/ContactForm.tsx`

> **Use `frontend-design` skill** for visual quality on this task.

- [ ] **Step 1: Create `frontend/app/[locale]/despre/page.tsx`**

```tsx
import { getTranslations } from 'next-intl/server';
import type { Metadata } from 'next';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'about' });
  return { title: t('title') };
}

export default async function AboutPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'about' });

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-gray-900 mb-8">{t('title')}</h1>
      <div className="prose prose-lg prose-gray max-w-none mb-12">
        <p>{t('p1')}</p>
        <p>{t('p2')}</p>
        <p>{t('p3')}</p>
      </div>
      <div className="bg-white rounded-2xl shadow-sm p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('contact_title')}</h2>
        <dl className="space-y-2 text-gray-700">
          <div className="flex gap-3">
            <dt className="font-semibold w-20 shrink-0">Adresă</dt>
            <dd>{t('address')}</dd>
          </div>
          <div className="flex gap-3">
            <dt className="font-semibold w-20 shrink-0">Telefon</dt>
            <dd><a href={`tel:${t('phone').replace(/\s/g, '')}`} className="text-blue-700 hover:underline">{t('phone')}</a></dd>
          </div>
          <div className="flex gap-3">
            <dt className="font-semibold w-20 shrink-0">Email</dt>
            <dd><a href={`mailto:${t('email')}`} className="text-blue-700 hover:underline">{t('email')}</a></dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/components/ContactForm.tsx`**

```tsx
'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { submitContact } from '@/lib/api';

export default function ContactForm() {
  const t = useTranslations('contact');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('sending');
    try {
      await submitContact({ name, email, phone: phone || undefined, message });
      setStatus('success');
      setName(''); setEmail(''); setPhone(''); setMessage('');
    } catch {
      setStatus('error');
    }
  }

  if (status === 'success') {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-green-800 text-center">
        {t('success')}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('name')}</label>
        <input required minLength={2} value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('email')}</label>
        <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('phone')}</label>
        <input value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">{t('message')}</label>
        <textarea required minLength={10} rows={5} value={message} onChange={(e) => setMessage(e.target.value)} className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
      </div>
      {status === 'error' && <p className="text-red-600 text-sm">{t('error')}</p>}
      <button
        type="submit"
        disabled={status === 'sending'}
        className="w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {status === 'sending' ? t('sending') : t('send')}
      </button>
    </form>
  );
}
```

- [ ] **Step 3: Create `frontend/app/[locale]/contact/page.tsx`**

```tsx
import { getTranslations } from 'next-intl/server';
import type { Metadata } from 'next';
import ContactForm from '@/components/ContactForm';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'contact' });
  return { title: t('title') };
}

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'contact' });

  return (
    <div className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-gray-900 mb-2">{t('title')}</h1>
      <p className="text-gray-500 mb-10">{t('subtitle')}</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Form */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('form_title')}</h2>
          <ContactForm />
        </div>

        {/* Info */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('info_title')}</h2>
          <dl className="space-y-4 text-gray-700">
            <div>
              <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Adresă</dt>
              <dd>{t('address')}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Telefon</dt>
              <dd><a href={`tel:${t('phone_val').replace(/\s/g, '')}`} className="text-blue-700 hover:underline font-semibold">{t('phone_val')}</a></dd>
            </div>
            <div>
              <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Email</dt>
              <dd><a href={`mailto:${t('email_val')}`} className="text-blue-700 hover:underline">{t('email_val')}</a></dd>
            </div>
            <div>
              <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Program</dt>
              <dd className="text-sm">{t('hours')}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -15
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/app/\[locale\]/despre/ frontend/app/\[locale\]/contact/ frontend/components/ContactForm.tsx && git commit -m "feat: add About and Contact pages with contact form"
```

---

## Task 10: SEO — metadata, sitemap, robots, not-found

**Files:**
- Create: `frontend/app/sitemap.ts`
- Create: `frontend/app/robots.ts`
- Create: `frontend/app/[locale]/not-found.tsx`
- Modify: `frontend/app/[locale]/layout.tsx` — add `alternates` hreflang

- [ ] **Step 1: Create `frontend/app/sitemap.ts`**

```typescript
import type { MetadataRoute } from 'next';
import { getCars } from '@/lib/api';

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://covareli.ro';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRo = ['/', '/masini', '/despre', '/contact', '/rezervare'];
  const staticEn = ['/en', '/en/cars', '/en/about', '/en/contact', '/en/booking'];

  const staticEntries: MetadataRoute.Sitemap = [
    ...staticRo.map((p) => ({ url: `${BASE}${p}`, priority: p === '/' ? 1.0 : 0.8 })),
    ...staticEn.map((p) => ({ url: `${BASE}${p}`, priority: p === '/en' ? 0.9 : 0.7 })),
  ];

  let carEntries: MetadataRoute.Sitemap = [];
  try {
    const cars = await getCars();
    carEntries = cars.flatMap((car) => [
      { url: `${BASE}/masini/${car.slug}`, priority: 0.9 },
      { url: `${BASE}/en/cars/${car.slug}`, priority: 0.8 },
    ]);
  } catch {}

  return [...staticEntries, ...carEntries];
}
```

- [ ] **Step 2: Create `frontend/app/robots.ts`**

```typescript
import type { MetadataRoute } from 'next';

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://covareli.ro';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: '*', allow: '/', disallow: ['/api/', '/rezervare/confirmare'] },
    sitemap: `${BASE}/sitemap.xml`,
  };
}
```

- [ ] **Step 3: Create `frontend/app/[locale]/not-found.tsx`**

```tsx
import { useTranslations } from 'next-intl';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center text-center px-4">
      <div>
        <p className="text-6xl font-bold text-gray-200 mb-4">404</p>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Pagina nu a fost găsită</h1>
        <Link href="/" className="bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-800 transition-colors">
          Înapoi acasă
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Add NEXT_PUBLIC_SITE_URL to .env.local**

Append to `frontend/.env.local`:
```
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

And to `frontend/.env.local.example`:
```
NEXT_PUBLIC_SITE_URL=https://covareli.ro
```

- [ ] **Step 5: Verify final build**

```bash
cd /home/ubuntu/work/covareli/frontend && npm run build 2>&1 | tail -20
```

Expected: build succeeds, route table shows all pages.

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/work/covareli && git add frontend/app/sitemap.ts frontend/app/robots.ts frontend/app/\[locale\]/not-found.tsx frontend/frontend/.env.local.example && git commit -m "feat: add sitemap.xml, robots.txt, and 404 page"
```

---

## Self-Review Against Spec

| Spec requirement | Task |
|---|---|
| Next.js SSR, TypeScript, Tailwind | Task 1 |
| RO at `/`, EN at `/en/...` with next-intl | Task 1 |
| Localized pathnames (/masini vs /en/cars) | Task 1 |
| Language switcher in header | Task 4 |
| Home: hero + search form | Task 5 |
| Home: benefits + how it works + CTA | Task 5 |
| Cars list with filters (body, fuel, transmission, seats) | Task 6 |
| Availability filter (from/to passed to API) | Task 6 |
| Car detail: gallery, specs, features, pricing table | Task 7 |
| Booking flow: form → POST /api/bookings → confirmation | Task 8 |
| Confirmation page with booking ID | Task 8 |
| About page | Task 9 |
| Contact page with form → POST /api/contact | Task 9 |
| SEO: sitemap.xml, robots.txt, per-page metadata | Task 10 |
| CORS on backend for dev | Task 1 |
| Typed API client | Task 2 |

**Gaps found:** None critical. "hreflang" meta tags (mentioned in spec) are handled by next-intl automatically when `alternates` is configured — no extra task needed.

**Placeholder scan:** No TBDs. All steps have complete code.

**Type consistency:** All components import from `@/lib/types`. `Car`, `Location`, `PriceBreakdown` are defined once and used consistently. `mediaUrl()` and API functions referenced by name consistently across Tasks 2 and 5-9.
