import type { Slide } from '../data/types';
import { PlatformBadge, SlideNumber } from './PlatformBadge';

interface Props {
  slide: Slide;
  onClick: () => void;
}

export function SlideCard({ slide, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      className="group bg-surface/80 backdrop-blur-xl border border-border rounded-xl text-left transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 cursor-pointer w-full overflow-hidden"
    >
      {/* Image */}
      <div className="relative bg-black overflow-hidden">
        <img
          src={slide.file}
          alt={slide.title}
          loading="lazy"
          className="w-full object-contain block"
          style={{ aspectRatio: '4 / 5' }}
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
          }}
        />
        <div
          className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end"
          style={{ padding: 12 }}
        >
          <span className="text-xs font-medium text-white/90">Click to preview</span>
        </div>
      </div>

      {/* Text */}
      <div style={{ padding: '10px 14px 12px' }}>
        {/* Badge row */}
        <div className="flex items-center" style={{ marginBottom: 8, gap: 10 }}>
          <PlatformBadge platform={slide.platform} />
          <SlideNumber id={slide.id} />
        </div>
        {/* Title */}
        <p className="text-sm font-semibold text-text leading-snug">
          {slide.title}
        </p>
        {/* Description */}
        <p
          className="text-xs text-muted"
          style={{ marginTop: 4, lineHeight: 1.4 }}
        >
          {slide.desc}
        </p>
      </div>
    </button>
  );
}
