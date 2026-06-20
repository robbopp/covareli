import { getTranslations } from 'next-intl/server';
import Link from 'next/link';
import type { Metadata } from 'next';
import SearchForm from '@/components/SearchForm';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'home.hero' });
  return { title: t('title') };
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale });

  const benefits: { title: string; desc: string }[] = t.raw('home.benefits.items');
  const steps: { step: string; title: string; desc: string }[] = t.raw('home.how.steps');

  const carsPath = locale === 'ro' ? '/masini' : '/en/cars';

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-700 to-blue-900 text-white">
        <div className="max-w-6xl mx-auto px-4 py-20">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 max-w-2xl leading-tight">
            {t('home.hero.title')}
          </h1>
          <p className="text-blue-100 text-lg mb-10 max-w-xl">
            {t('home.hero.subtitle')}
          </p>
          <SearchForm />
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">{t('home.benefits.title')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((b, i) => (
              <div key={i} className="text-center p-6 rounded-2xl bg-gray-50 hover:shadow-md transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-blue-700 font-bold text-lg">{i + 1}</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{b.title}</h3>
                <p className="text-sm text-gray-500">{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">{t('home.how.title')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {steps.map((s, i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-full bg-blue-700 text-white flex items-center justify-center text-2xl font-bold mb-4">
                  {s.step}
                </div>
                <h3 className="font-semibold text-lg mb-2">{s.title}</h3>
                <p className="text-gray-500 text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-blue-700 text-white text-center">
        <div className="max-w-2xl mx-auto px-4">
          <h2 className="text-3xl font-bold mb-3">{t('home.cta.title')}</h2>
          <p className="text-blue-100 mb-8">{t('home.cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="tel:+40749323172"
              className="bg-white text-blue-700 font-semibold px-8 py-3 rounded-xl hover:bg-blue-50 transition-colors"
            >
              {t('home.cta.phone_label')}
            </a>
            <Link
              href={carsPath}
              className="border-2 border-white text-white font-semibold px-8 py-3 rounded-xl hover:bg-blue-800 transition-colors"
            >
              {t('home.cta.browse_label')}
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
