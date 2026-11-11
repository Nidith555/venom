import React from 'react';
import { VenomLogo } from './VenomLogo';

interface SymbioteLoaderProps {
  progress?: number;
}

export const SymbioteLoader: React.FC<SymbioteLoaderProps> = ({ progress = 100 }) => {
  return (
    <div className="fixed inset-0 bg-[#000000] z-50 flex flex-col items-center justify-center select-none">
      <div className="animate-pulse duration-1000">
        <VenomLogo size={90} />
      </div>
      <h2 className="mt-8 text-sm sm:text-base font-black tracking-[0.35em] text-[#f4f4f6] font-['Orbitron'] uppercase">
        INITIALIZING SYMBIOTE BOND...
      </h2>
      <div className="w-48 h-1 bg-[#111214] mt-4 overflow-hidden relative">
        <div
          className="h-full bg-[#f4f4f6] transition-all duration-300 shadow-[0_0_10px_#f4f4f6]"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
