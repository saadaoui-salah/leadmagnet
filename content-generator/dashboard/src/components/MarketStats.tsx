import { TrendingUp, Home, Building2, Clock } from 'lucide-react';
import { marketData } from '../data/mockData';

function formatCurrency(n: number) {
  return '$' + n.toLocaleString();
}

const stats = [
  {
    label: 'Median Rent',
    value: formatCurrency(marketData.medianRent),
    change: `+${marketData.rentGrowth30d}%`,
    changePositive: true,
    icon: TrendingUp,
    color: '#2BEE34',
  },
  {
    label: 'Median Home Price',
    value: formatCurrency(marketData.medianHomePrice),
    change: `+${marketData.homeGrowth30d}%`,
    changePositive: true,
    icon: Home,
    color: '#00D4FF',
  },
  {
    label: 'Active Listings',
    value: marketData.activeListings.toString(),
    change: null,
    icon: Building2,
    color: '#F5F7FA',
  },
  {
    label: 'Avg Days on Market',
    value: `${marketData.avgDaysOnMarket}d`,
    change: null,
    icon: Clock,
    color: '#FFC857',
  },
];

export function MarketStats() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-surface/80 backdrop-blur-xl border border-border rounded-xl hover:border-primary/20 transition-colors"
          style={{ padding: '18px 22px' }}
        >
          <div className="flex items-center" style={{ gap: 8, marginBottom: 12 }}>
            <stat.icon
              style={{ width: 16, height: 16, color: '#94A3B8', flexShrink: 0 }}
            />
            <p
              style={{
                fontSize: 11,
                color: '#94A3B8',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                fontWeight: 500,
              }}
              className="truncate"
            >
              {stat.label}
            </p>
          </div>
          <p style={{ fontSize: 24, fontWeight: 700, color: stat.color }}>
            {stat.value}
          </p>
          {stat.change && (
            <p
              style={{
                fontSize: 12,
                marginTop: 8,
                color: stat.changePositive ? '#2BEE34' : '#FF5C7A',
              }}
            >
              {stat.change} this month
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
