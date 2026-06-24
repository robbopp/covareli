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
  payment_url: string;
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
