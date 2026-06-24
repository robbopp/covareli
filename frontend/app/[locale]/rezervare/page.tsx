'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { getCar, getLocations, createBooking } from '@/lib/api';
import type { Car, Location, PriceBreakdown } from '@/lib/types';

function CheckoutContent() {
  const t = useTranslations('checkout');
  const locale = useLocale();
  const router = useRouter();
  const searchParams = useSearchParams();

  const carSlug = searchParams.get('car') ?? '';
  const fromParam = searchParams.get('from') ?? '';
  const toParam = searchParams.get('to') ?? '';
  const pickupParam = searchParams.get('pickup') ?? '';
  const dropoffParam = searchParams.get('dropoff') ?? '';

  const [car, setCar] = useState<Car | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);

  // Form fields
  const [fromDate, setFromDate] = useState(fromParam ? fromParam.split('T')[0] : '');
  const [toDate, setToDate] = useState(toParam ? toParam.split('T')[0] : '');
  const [pickupId, setPickupId] = useState(pickupParam);
  const [dropoffId, setDropoffId] = useState(dropoffParam);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!carSlug) {
      setLoading(false);
      return;
    }
    Promise.all([getCar(carSlug), getLocations()])
      .then(([carData, locs]) => {
        setCar(carData);
        setLocations(locs);
        if (!pickupId && locs.length > 0) setPickupId(locs[0].id);
        if (!dropoffId && locs.length > 0) setDropoffId(locs[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [carSlug]); // eslint-disable-line react-hooks/exhaustive-deps

  // Price calculation
  const pickupLocation = locations.find((l) => l.id === pickupId);
  const dropoffLocation = locations.find((l) => l.id === dropoffId);

  function calcDays(): number {
    if (!fromDate || !toDate) return 0;
    const from = new Date(fromDate);
    const to = new Date(toDate);
    const diff = Math.ceil((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  }

  function getPricePerDay(days: number): number {
    if (!car || days === 0) return 0;
    const tiers = [...car.price_tiers].sort((a, b) => a.min_days - b.min_days);
    let price = tiers[0]?.price_per_day ?? 0;
    for (const tier of tiers) {
      if (days >= tier.min_days) {
        price = tier.price_per_day;
      }
    }
    return price;
  }

  const days = calcDays();
  const pricePerDay = getPricePerDay(days);
  const carTotal = days * pricePerDay;
  const pickupFee = pickupLocation?.fee ?? 0;
  const dropoffFee = dropoffLocation?.fee ?? 0;
  const total = carTotal + pickupFee + dropoffFee;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!car) return;
    setError('');
    setSubmitting(true);
    try {
      const result = await createBooking({
        car_id: car.id,
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
        pickup_at: fromDate ? `${fromDate}T10:00:00` : fromParam,
        dropoff_at: toDate ? `${toDate}T10:00:00` : toParam,
        pickup_location_id: pickupId,
        dropoff_location_id: dropoffId,
      });
      window.location.href = result.payment_url;
    } catch {
      setError(t('error_generic'));
      setSubmitting(false);
    }
  }

  if (!carSlug) {
    const carsPath = locale === 'ro' ? '/masini' : '/en/cars';
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <p className="text-gray-600 mb-6">{t('no_car')}</p>
        <a href={carsPath} className="bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-800 transition-colors">
          {locale === 'ro' ? 'Vezi mașinile' : 'Browse cars'}
        </a>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center text-gray-500">
        Se încarcă...
      </div>
    );
  }

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">{t('title')}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form */}
        <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-6">
          {/* Period */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">{t('period')}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('pickup')}
                </label>
                <input
                  type="date"
                  min={today}
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  required
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('dropoff')}
                </label>
                <input
                  type="date"
                  min={fromDate || today}
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  required
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Locations */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Locații</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('pickup')}
                </label>
                <select
                  value={pickupId}
                  onChange={(e) => setPickupId(e.target.value)}
                  required
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">— Selectați —</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {locale === 'ro' ? l.name.ro : l.name.en}
                      {l.fee > 0 ? ` (+${l.fee} lei)` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('dropoff')}
                </label>
                <select
                  value={dropoffId}
                  onChange={(e) => setDropoffId(e.target.value)}
                  required
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">— Selectați —</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {locale === 'ro' ? l.name.ro : l.name.en}
                      {l.fee > 0 ? ` (+${l.fee} lei)` : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Customer details */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">{t('customer_title')}</h2>
            <div className="space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('name')}
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Ion Popescu"
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('email')}
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="ion@exemplu.ro"
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {t('phone')}
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  placeholder="+40 7xx xxx xxx"
                  className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || days === 0 || !pickupId || !dropoffId}
            className="w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl transition-colors text-base"
          >
            {submitting ? t('submitting') : t('submit')}
          </button>
        </form>

        {/* Summary */}
        <aside className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sticky top-6">
            <h2 className="font-semibold text-gray-900 mb-4">{t('summary')}</h2>

            {car && (
              <p className="text-gray-800 font-medium mb-4">
                {car.brand} {car.model} {car.year}
              </p>
            )}

            <div className="space-y-3 text-sm">
              {fromDate && toDate && (
                <div className="flex justify-between text-gray-600">
                  <span>{t('period')}</span>
                  <span className="font-medium text-gray-900">
                    {fromDate} → {toDate}
                  </span>
                </div>
              )}
              {days > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>{t('days', { n: days })}</span>
                  <span className="font-medium text-gray-900">{t('price_per_day', { price: pricePerDay })}</span>
                </div>
              )}
              {days > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal mașină</span>
                  <span className="font-medium text-gray-900">{carTotal} lei</span>
                </div>
              )}
              {pickupFee > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>{t('pickup')} ({t('location_fee')})</span>
                  <span className="font-medium text-gray-900">{pickupFee} lei</span>
                </div>
              )}
              {dropoffFee > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>{t('dropoff')} ({t('location_fee')})</span>
                  <span className="font-medium text-gray-900">{dropoffFee} lei</span>
                </div>
              )}
            </div>

            {days > 0 && (
              <>
                <hr className="my-4 border-gray-100" />
                <div className="flex justify-between font-bold text-gray-900 text-lg">
                  <span>{t('total')}</span>
                  <span>{total} lei</span>
                </div>
              </>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default function RezervarePage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-6xl mx-auto px-4 py-20 text-center text-gray-500">
          Se încarcă...
        </div>
      }
    >
      <CheckoutContent />
    </Suspense>
  );
}
