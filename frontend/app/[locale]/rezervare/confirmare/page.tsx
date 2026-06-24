import { Suspense } from 'react';
import { getTranslations } from 'next-intl/server';
import Link from 'next/link';
import type { Metadata } from 'next';
import ConfirmationContent from './ConfirmationContent';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'confirmation' });
  return { title: t('title') };
}

export default async function ConfirmarePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'confirmation' });

  return (
    <div className="max-w-2xl mx-auto px-4 py-20 text-center">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-10">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-4">{t('title')}</h1>
        <p className="text-gray-600 mb-6 leading-relaxed">{t('message')}</p>

        <Suspense fallback={null}>
          <ConfirmationContent bookingIdLabel={t('booking_id', { id: '...' })} />
        </Suspense>

        <p className="text-sm text-gray-500 mb-8">
          {t('contact_us', { phone: '+40 749 323 172' })}
        </p>

        <Link
          href="/"
          className="inline-block bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-800 transition-colors"
        >
          {t('back_home')}
        </Link>
      </div>
    </div>
  );
}
