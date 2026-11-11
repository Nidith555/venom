import React from 'react';

interface VenomLogoProps {
  className?: string;
  size?: number;
}

export const VenomLogo: React.FC<VenomLogoProps> = ({ className = '', size = 52 }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 60 60"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`venom-spider-svg ${className}`}
      style={{
        filter: 'drop-shadow(0 0 10px rgba(244, 244, 246, 0.45))',
      }}
    >
      {/* Spider Head & Body */}
      <ellipse cx="30" cy="28" rx="10" ry="13" fill="#f4f4f6" />
      <ellipse cx="30" cy="20" rx="7" ry="6" fill="#f4f4f6" />

      {/* Menacing Venom Eyes (Sharp, Angular) */}
      <path
        d="M24 16 C25 18, 28 22, 29 23 C27 23, 24 21, 23 18 Z"
        fill="#000000"
      />
      <path
        d="M36 16 C35 18, 32 22, 31 23 C33 23, 36 21, 37 18 Z"
        fill="#000000"
      />

      {/* Organic Left Spider Legs (Upper, Middle, Lower) */}
      <path
        d="M21 23 C14 17, 8 13, 3 8"
        stroke="#f4f4f6"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M20 27 C12 25, 6 23, 2 18"
        stroke="#f4f4f6"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M20 31 C10 33, 5 39, 4 48"
        stroke="#f4f4f6"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M22 35 C14 41, 9 49, 8 56"
        stroke="#f4f4f6"
        strokeWidth="2"
        strokeLinecap="round"
      />

      {/* Organic Right Spider Legs (Upper, Middle, Lower) */}
      <path
        d="M39 23 C46 17, 52 13, 57 8"
        stroke="#f4f4f6"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M40 27 C48 25, 54 23, 58 18"
        stroke="#f4f4f6"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M40 31 C50 33, 55 39, 56 48"
        stroke="#f4f4f6"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M38 35 C46 41, 51 49, 52 56"
        stroke="#f4f4f6"
        strokeWidth="2"
        strokeLinecap="round"
      />

      {/* Razor Teeth / Symbiote Jaw Accent */}
      <path
        d="M26 40 C28 44, 32 44, 34 40"
        stroke="#f4f4f6"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
};
