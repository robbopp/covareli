'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useLocale, useTranslations } from 'next-intl';
import { mediaUrl } from '@/lib/api';
import type { Car } from '@/lib/types';

interface Props {
  car: Car;
}

export default function CarCard({ car }: Props) {
  const locale = useLocale();
  const t = useTranslations('cars');
  const detailPath = locale === 'ro' ? `/masini/${car.slug}` : `/en/cars/${car.slug}`;
  const thumb = car.images[0] ? mediaUrl(car.images[0]) : null;

  return (
    <div className="bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col">
      <div className="aspect-video bg-gray-100 relative">
        {thumb ? (
          <Image
            src={thumb}
            alt={`${car.brand} ${car.model}`}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 33vw"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-4xl select-none">
            🚗
          </div>
        )}
      </div>
      <div className="p-5 flex flex-col flex-1">
        <h3 className="font-bold text-lg text-gray-900">
          {car.brand} {car.model}{' '}
          <span className="text-gray-400 font-normal text-base">{car.year}</span>
        </h3>
        <div className="flex flex-wrap gap-2 mt-2 mb-4">
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
            {t(`fuel_${car.fuel}` as `fuel_${typeof car.fuel}`)}
          </span>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
            {t(`transmission_${car.transmission}` as `transmission_${typeof car.transmission}`)}
          </span>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
            {t('seats', { n: car.seats })}
          </span>
        </div>
        <p className="text-blue-700 font-semibold mt-auto mb-4">
          {t('from_price', { price: car.price_from })}
        </p>
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
