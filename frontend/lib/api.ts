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
