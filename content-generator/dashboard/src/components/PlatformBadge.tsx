interface PlatformBadgeProps {
  platform: 'linkedin' | 'instagram' | 'youtube' | 'facebook' | 'threads' | 'x';
  size?: 'sm' | 'md';
}

const styles: Record<string, { background: string; color: string }> = {
  linkedin: {
    background: 'rgba(0,212,255,0.12)',
    color: '#00D4FF',
  },
  instagram: {
    background: 'rgba(236,72,153,0.12)',
    color: '#F472B6',
  },
  youtube: {
    background: 'rgba(255,0,0,0.12)',
    color: '#FF4444',
  },
  facebook: {
    background: 'rgba(24,119,242,0.12)',
    color: '#1877F2',
  },
  threads: {
    background: 'rgba(0,0,0,0.12)',
    color: '#FFFFFF',
  },
  x: {
    background: 'rgba(255,255,255,0.12)',
    color: '#FFFFFF',
  },
};

const sizes = {
  sm: { padding: '2px 8px', fontSize: 10 },
  md: { padding: '3px 10px', fontSize: 11 },
} as const;

export function PlatformBadge({ platform, size = 'sm' }: PlatformBadgeProps) {
  const s = styles[platform];
  const sz = sizes[size];

  return (
    <span
      style={{
        display: 'inline-block',
        padding: sz.padding,
        borderRadius: 4,
        fontSize: sz.fontSize,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        background: s.background,
        color: s.color,
      }}
    >
      {platform}
    </span>
  );
}

interface SlideNumberProps {
  id: number;
}

export function SlideNumber({ id }: SlideNumberProps) {
  return (
    <span
      style={{
        fontSize: 11,
        color: '#94A3B8',
        fontFamily: 'monospace',
        letterSpacing: '0.05em',
      }}
    >
      #{String(id).padStart(2, '0')}
    </span>
  );
}
