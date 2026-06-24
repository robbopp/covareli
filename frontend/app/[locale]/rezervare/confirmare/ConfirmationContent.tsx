'use client';

import { useSearchParams } from 'next/navigation';

interface Props {
  bookingIdLabel: string;
}

export default function ConfirmationContent({ bookingIdLabel }: Props) {
  const searchParams = useSearchParams();
  const bookingId = searchParams.get('booking') ?? '';
  const shortId = bookingId ? bookingId.slice(0, 8).toUpperCase() : '';

  if (!shortId) return null;

  // Replace the '...' placeholder in the label with the actual short id
  const label = bookingIdLabel.replace('...', shortId);

  return (
    <div className="bg-gray-50 rounded-xl px-6 py-4 mb-6 text-sm font-mono text-gray-700">
      {label}
    </div>
  );
}
