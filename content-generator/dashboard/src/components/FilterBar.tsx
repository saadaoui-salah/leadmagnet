import type { FilterTab } from '../data/types';

interface Props {
  active: FilterTab;
  onChange: (tab: FilterTab) => void;
  counts: { all: number; linkedin: number; instagram: number; youtube: number; facebook: number; threads: number; x: number };
}

const tabs: { key: FilterTab; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'linkedin', label: 'LinkedIn' },
  { key: 'instagram', label: 'Instagram' },
];

export function FilterBar({ active, onChange, counts }: Props) {
  return (
    <div className="flex items-center" style={{ gap: 10 }}>
      {tabs.map((tab) => {
        const isActive = active === tab.key;
        return (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            className="flex items-center rounded-lg transition-all"
            style={{
              padding: '6px 14px',
              gap: 8,
              fontSize: 14,
              fontWeight: 500,
              background: isActive ? 'rgba(43,238,52,0.1)' : 'transparent',
              border: `1px solid ${isActive ? 'rgba(43,238,52,0.4)' : 'rgba(148,163,184,0.18)'}`,
              color: isActive ? '#2BEE34' : '#94A3B8',
            }}
          >
            <span>{tab.label}</span>
            <span style={{ fontSize: 12, opacity: 0.5 }}>{counts[tab.key]}</span>
          </button>
        );
      })}
    </div>
  );
}
