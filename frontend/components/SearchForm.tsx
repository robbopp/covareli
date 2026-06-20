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
