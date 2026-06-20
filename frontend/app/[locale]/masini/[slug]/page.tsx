import { getTranslations } from 'next-intl/server';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ApiError, getCar } from '@/lib/api';
import type { BodyType, FuelType, Transmission } from '@/lib/types';
import CarGallery from '@/components/CarGallery';
import PriceTierTable from '@/components/PriceTierTable';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
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

  const specRows: [string, string][] = [
    ['Tip', t(`cars.body_${car.body_type}` as `cars.body_${BodyType}`)],
    ['Combustibil', t(`cars.fuel_${car.fuel}` as `cars.fuel_${FuelType}`)],
    ['Transmisie', t(`cars.transmission_${car.transmission}` as `cars.transmission_${Transmission}`)],
    ['Locuri', String(car.seats)],
    ['Uși', String(car.doors)],
    ...(car.engine ? ([['Motor', car.engine]] as [string, string][]) : []),
  ];

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

          {desc && (
            <p className="text-gray-600 mb-6 leading-relaxed">{desc}</p>
          )}

          {/* Specs */}
          <h2 className="font-semibold text-gray-900 mb-3">{t('car_detail.specs')}</h2>
          <div className="grid grid-cols-2 gap-2 mb-6">
            {specRows.map(([label, value]) => (
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
