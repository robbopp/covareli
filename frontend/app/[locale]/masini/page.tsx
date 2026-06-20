import { getTranslations } from 'next-intl/server';
import type { Metadata } from 'next';
import { getCars } from '@/lib/api';
import type { Car } from '@/lib/types';
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
  searchParams: Promise<{ from?: string; to?: string }>;
}) {
  await params;
  const sp = await searchParams;

  const cars = await getCars({
    from: sp.from,
    to: sp.to,
  }).catch(() => [] as Car[]);

  return <CarsClientPage initialCars={cars} />;
}
