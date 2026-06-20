import { getLocale, getTranslations } from 'next-intl/server';
import type { PriceTier } from '@/lib/types';

interface Props {
  tiers: PriceTier[];
}

export default async function PriceTierTable({ tiers }: Props) {
  const locale = await getLocale();
  const t = await getTranslations({ locale, namespace: 'car_detail' });

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="bg-gray-50">
          <th className="text-left px-4 py-2 font-semibold text-gray-600 rounded-tl-lg">
            {t('pricing')}
          </th>
          <th className="text-right px-4 py-2 font-semibold text-gray-600 rounded-tr-lg">
            Lei/zi
          </th>
        </tr>
      </thead>
      <tbody>
        {tiers.map((tier, i) => (
          <tr key={i} className="border-t border-gray-100">
            <td className="px-4 py-2 text-gray-700">
              {tier.max_days
                ? t('pricing_days', { min: tier.min_days, max: tier.max_days })
                : t('pricing_days_plus', { min: tier.min_days })}
            </td>
            <td className="px-4 py-2 text-right font-semibold text-blue-700">
              {tier.price_per_day}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
