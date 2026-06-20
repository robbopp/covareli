'use client';

import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';

export default function Header() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  const otherLocale = locale === 'ro' ? 'en' : 'ro';

  function switchLocale() {
    const withoutLocale = pathname.replace(/^\/(en)(\/|$)/, '/');
    if (otherLocale === 'en') {
      router.push(`/en${withoutLocale === '/' ? '' : withoutLocale}`);
    } else {
      router.push(withoutLocale || '/');
    }
  }

  const navLinks = [
    { href: locale === 'ro' ? '/masini' : '/en/cars', label: t('cars') },
    { href: locale === 'ro' ? '/despre' : '/en/about', label: t('about') },
    { href: '/contact', label: t('contact') },
  ];

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16">
        <Link href={locale === 'ro' ? '/' : '/en'} className="text-xl font-bold text-blue-700 tracking-tight">
          Covareli
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-gray-600 hover:text-blue-700 font-medium transition-colors"
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={switchLocale}
            className="ml-4 px-3 py-1 border border-gray-300 rounded text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            {otherLocale.toUpperCase()}
          </button>
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-gray-600"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          <span className="block w-6 h-0.5 bg-current mb-1" />
          <span className="block w-6 h-0.5 bg-current mb-1" />
          <span className="block w-6 h-0.5 bg-current" />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white px-4 py-3 flex flex-col gap-3">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-gray-700 font-medium py-1"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={() => { switchLocale(); setMenuOpen(false); }}
            className="self-start px-3 py-1 border border-gray-300 rounded text-sm font-medium"
          >
            {otherLocale.toUpperCase()}
          </button>
        </div>
      )}
    </header>
  );
}
