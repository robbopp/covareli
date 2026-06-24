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
