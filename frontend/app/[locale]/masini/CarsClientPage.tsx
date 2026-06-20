'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import CarCard from '@/components/CarCard';
import type { BodyType, Car, FuelType, Transmission } from '@/lib/types';

interface Props {
  initialCars: Car[];
}

const BODY_TYPES: BodyType[] = ['hatchback', 'sedan', 'suv', 'van', 'wagon'];
const FUEL_TYPES: FuelType[] = ['petrol', 'diesel', 'hybrid', 'electric'];
const TRANSMISSIONS: Transmission[] = ['manual', 'automatic'];

export default function CarsClientPage({ initialCars }: Props) {
  const t = useTranslations('cars');
  const [bodyType, setBodyType] = useState<BodyType | ''>('');
  const [fuel, setFuel] = useState<FuelType | ''>('');
  const [transmission, setTransmission] = useState<Transmission | ''>('');
  const [seatsMin, setSeatsMin] = useState('');

  const filtered = initialCars.filter((car) => {
    if (bodyType && car.body_type !== bodyType) return false;
    if (fuel && car.fuel !== fuel) return false;
    if (transmission && car.transmission !== transmission) return false;
    if (seatsMin && car.seats < parseInt(seatsMin, 10)) return false;
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
              <button onClick={reset} className="text-xs text-blue-700 hover:underline">
                {t('filters.reset')}
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">
                  {t('filters.body_type')}
                </label>
                <select
                  value={bodyType}
                  onChange={(e) => setBodyType(e.target.value as BodyType | '')}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">{t('filters.all')}</option>
                  {BODY_TYPES.map((bt) => (
                    <option key={bt} value={bt}>{t(`body_${bt}` as `body_${BodyType}`)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">
                  {t('filters.fuel')}
                </label>
                <select
                  value={fuel}
                  onChange={(e) => setFuel(e.target.value as FuelType | '')}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">{t('filters.all')}</option>
                  {FUEL_TYPES.map((f) => (
                    <option key={f} value={f}>{t(`fuel_${f}` as `fuel_${FuelType}`)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">
                  {t('filters.transmission')}
                </label>
                <select
                  value={transmission}
                  onChange={(e) => setTransmission(e.target.value as Transmission | '')}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">{t('filters.all')}</option>
                  {TRANSMISSIONS.map((tr) => (
                    <option key={tr} value={tr}>{t(`transmission_${tr}` as `transmission_${Transmission}`)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">
                  {t('filters.seats_min')}
                </label>
                <input
                  type="number"
                  min="2"
                  max="9"
                  value={seatsMin}
                  onChange={(e) => setSeatsMin(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="2"
                />
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
              {filtered.map((car) => (
                <CarCard key={car.id} car={car} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
