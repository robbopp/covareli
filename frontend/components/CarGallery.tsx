'use client';

import Image from 'next/image';
import { useState } from 'react';
import { mediaUrl } from '@/lib/api';

interface Props {
  images: string[];
  alt: string;
}

export default function CarGallery({ images, alt }: Props) {
  const [active, setActive] = useState(0);

  if (images.length === 0) {
    return (
      <div className="aspect-video bg-gray-100 rounded-2xl flex items-center justify-center text-gray-300 text-6xl select-none">
        🚗
      </div>
    );
  }

  return (
    <div>
      <div className="aspect-video relative rounded-2xl overflow-hidden bg-gray-100 mb-3">
        <Image
          src={mediaUrl(images[active])}
          alt={alt}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 55vw"
          priority
        />
      </div>
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((img, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
              className={`relative w-20 h-14 rounded-lg overflow-hidden shrink-0 border-2 transition-colors ${
                i === active ? 'border-blue-700' : 'border-transparent'
              }`}
            >
              <Image
                src={mediaUrl(img)}
                alt=""
                fill
                className="object-cover"
                sizes="80px"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
