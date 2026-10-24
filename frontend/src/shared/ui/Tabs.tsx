import React from "react";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange, className = "" }) => {
  return (
    <div className={`border-b border-[#E2E5EA] ${className}`}>
      <nav className="-mb-px flex space-x-6 overflow-x-auto" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              aria-current={isActive ? "page" : undefined}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] rounded-t ${
                isActive
                  ? "border-[#0F766E] text-[#0F766E] font-semibold"
                  : "border-transparent text-[#5B6475] hover:text-[#1F2A44] hover:border-[#CBD2DC]"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`ml-1 rounded-full px-2 py-0.5 text-[11px] tabular-nums font-semibold ${
                    isActive ? "bg-[#0F766E]/10 text-[#0F766E]" : "bg-[#E2E5EA] text-[#5B6475]"
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};
