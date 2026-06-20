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
