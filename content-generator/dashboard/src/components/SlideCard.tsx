import { Play } from 'lucide-react';
import type { Slide } from '../data/types';
import { PlatformBadge, SlideNumber } from './PlatformBadge';

interface Props {
  slide: Slide;
  onClick: () => void;
}

export function SlideCard({ slide, onClick }: Props) {
  const isVideo = slide.isVideo;

  return (
    <button
      onClick={onClick}
      className="group bg-surface/80 backdrop-blur-xl border border-border rounded-xl text-left transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 cursor-pointer w-full overflow-hidden"
    >
      {/* Media */}
      <div className="relative bg-black overflow-hidden">
        {isVideo ? (
          <video
            src={slide.file}
            className="w-full object-contain block"
            style={{ aspectRatio: '9 / 16', maxHeight: 280 }}
            muted
            loop
            playsInline
            preload="metadata"
            onMouseEnter={(e) => (e.target as HTMLVideoElement).play().catch(() => {})}
            onMouseLeave={(e) => (e.target as HTMLVideoElement).pause()}
          />
        ) : (
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
        )}

        {/* Video play badge */}
        {isVideo && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center" style={{ width: 44, height: 44 }}>
              <Play className="w-5 h-5 text-white fill-white" />
            </div>
          </div>
        )}

        <div
          className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end"
          style={{ padding: 12 }}
        >
          <span className="text-xs font-medium text-white/90">
            {isVideo ? 'Click to play' : 'Click to preview'}
          </span>
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
