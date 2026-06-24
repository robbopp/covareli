import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import ContactForm from '@/components/ContactForm';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'contact' });
  return { title: t('title') };
}

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'contact' });

  return (
    <div className="max-w-5xl mx-auto px-4 py-14">
      <h1 className="text-4xl font-bold text-gray-900 mb-2">{t('title')}</h1>
      <p className="text-gray-500 text-lg mb-10">{t('subtitle')}</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Contact form */}
        <ContactForm />

        {/* Contact info + hours */}
        <aside className="space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4 text-lg">{t('info_title')}</h2>
            <ul className="space-y-4 text-sm text-gray-700">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{t('address')}</span>
              </li>
              <li className="flex items-center gap-3">
                <svg className="w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <a href={`tel:${t('phone_val').replace(/\s/g, '')}`} className="text-blue-700 hover:underline font-medium">
                  {t('phone_val')}
                </a>
              </li>
              <li className="flex items-center gap-3">
                <svg className="w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <a href={`mailto:${t('email_val')}`} className="text-blue-700 hover:underline font-medium">
                  {t('email_val')}
                </a>
              </li>
            </ul>
          </div>

          <div className="bg-blue-50 rounded-2xl border border-blue-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-3 text-lg">Program</h2>
            <p className="text-sm text-gray-700 leading-relaxed">{t('hours')}</p>
          </div>
        </aside>
      </div>
    </div>
  );
}
