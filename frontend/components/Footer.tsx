import Link from 'next/link';
import { useTranslations } from 'next-intl';

export default function Footer() {
  const t = useTranslations('footer');
  const year = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-gray-400 mt-auto">
      <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <p className="text-white font-bold text-lg mb-2">Covareli</p>
          <p className="text-sm">Str. Jupiter, nr. 1/12, Baciu, Cluj</p>
          <p className="text-sm">+40 749 323 172</p>
          <p className="text-sm">office@covareli.ro</p>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">{t('links_title')}</p>
          <ul className="space-y-1 text-sm">
            <li><Link href="/" className="hover:text-white transition-colors">Acasă</Link></li>
            <li><Link href="/masini" className="hover:text-white transition-colors">Mașini</Link></li>
            <li><Link href="/despre" className="hover:text-white transition-colors">Despre noi</Link></li>
            <li><Link href="/contact" className="hover:text-white transition-colors">Contact</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">{t('contact_title')}</p>
          <p className="text-sm">Luni–Vineri: 08:00–18:00</p>
          <p className="text-sm">Sâmbătă: 09:00–14:00</p>
        </div>
      </div>
      <div className="border-t border-gray-800 text-center text-xs py-4 text-gray-600">
        {t('rights', { year })}
      </div>
    </footer>
  );
}
