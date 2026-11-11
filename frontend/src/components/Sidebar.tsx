import React from 'react';
import { MessageSquare, Database, Cpu, Settings, Wrench } from 'lucide-react';
import { VenomLogo } from './VenomLogo';
import { useChatStore } from '../store/chatStore';

export const Sidebar: React.FC = () => {
  const { isConnected, currentModel, activeNav, setActiveNav } = useChatStore();

  const navItems = [
    { id: 'chat', label: 'Symbiote', icon: MessageSquare },
    { id: 'memory', label: 'Memory', icon: Database },
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'tools', label: 'Tools', icon: Wrench },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-60 flex-shrink-0 bg-[#0a0a0c]/90 border-r border-[#f4f4f6]/10 flex flex-col justify-between py-6 backdrop-blur-md relative z-10 select-none">
      {/* Brand Header */}
      <div>
        <div className="flex flex-col items-center px-4 pb-6 border-b border-[#f4f4f6]/10">
          <div className="hover:scale-105 transition-transform duration-300">
            <VenomLogo size={56} />
          </div>
          <h1 className="mt-3 text-lg font-black tracking-[0.3em] text-[#f4f4f6] font-['Orbitron']">
            VENOM
          </h1>
          <p className="text-[10px] uppercase tracking-widest text-[#f4f4f6]/40 mt-1">
            Symbiotic Intelligence
          </p>
        </div>

        {/* Navigation list */}
        <nav className="mt-6 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-xs tracking-wider uppercase transition-all duration-200 relative group ${
                  isActive
                    ? 'text-[#f4f4f6] bg-[#f4f4f6]/10 font-semibold'
                    : 'text-[#f4f4f6]/50 hover:text-[#f4f4f6] hover:bg-[#f4f4f6]/5'
                }`}
                style={{
                  clipPath: 'polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px)',
                }}
              >
                {/* Active indicator bar */}
                {isActive && (
                  <span className="absolute left-0 top-0 bottom-0 w-1 bg-[#00ff66] shadow-[0_0_8px_#00ff66]" />
                )}
                <Icon size={16} className={isActive ? 'text-[#00ff66]' : 'text-[#f4f4f6]/40 group-hover:text-[#f4f4f6]'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Host Vitals */}
      <div className="px-5 pt-4 border-t border-[#f4f4f6]/10">
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected
                ? 'bg-[#00ff66] shadow-[0_0_8px_#00ff66] animate-pulse'
                : 'bg-[#ff0033] shadow-[0_0_8px_#ff0033]'
            }`}
          />
          <span className="text-[11px] font-medium tracking-wider uppercase text-[#f4f4f6]/70">
            {isConnected ? 'Bond Active' : 'Offline Mode'}
          </span>
        </div>
        <div className="text-[10px] text-[#f4f4f6]/40 truncate tracking-wide font-mono">
          {currentModel}
        </div>
        <div className="text-[9px] text-[#00ff66]/60 truncate tracking-wider font-mono mt-0.5">
          VOICE: cgSgspJ2...
        </div>
      </div>
    </aside>
  );
};
