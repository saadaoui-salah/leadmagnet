import { useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import type { Slide } from '../data/types';
import { PlatformBadge } from './PlatformBadge';

interface Props {
  slides: Slide[];
  currentIndex: number;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
}

export function Lightbox({ slides, currentIndex, onClose, onPrev, onNext }: Props) {
  const slide = slides[currentIndex];

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') onNext();
      if (e.key === 'ArrowLeft') onPrev();
    },
    [onClose, onPrev, onNext]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  if (!slide) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center"
      style={{ padding: 24 }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {/* Close */}
      <button
        onClick={onClose}
        className="absolute p-2 rounded-full bg-surface/80 backdrop-blur-xl border border-border text-muted hover:text-text transition-colors z-10"
        style={{ top: 20, right: 20 }}
      >
        <X className="w-5 h-5" />
      </button>

      {/* Prev */}
      <button
        onClick={onPrev}
        className="absolute p-3 rounded-full bg-surface/80 backdrop-blur-xl border border-border text-muted hover:text-primary hover:border-primary/40 transition-all z-10"
        style={{ left: 20, top: '50%', transform: 'translateY(-50%)' }}
      >
        <ChevronLeft className="w-6 h-6" />
      </button>

      {/* Next */}
      <button
        onClick={onNext}
        className="absolute p-3 rounded-full bg-surface/80 backdrop-blur-xl border border-border text-muted hover:text-primary hover:border-primary/40 transition-all z-10"
        style={{ right: 20, top: '50%', transform: 'translateY(-50%)' }}
      >
        <ChevronRight className="w-6 h-6" />
      </button>

      {/* Media + info */}
      <div
        className="flex flex-col items-center"
        style={{ maxWidth: slide.isVideo ? 340 : 480, width: '100%' }}
      >
        {slide.isVideo ? (
          <video
            src={slide.file}
            className="w-full object-contain rounded-xl"
            style={{ maxHeight: '80vh', background: '#000' }}
            controls
            autoPlay
            loop
            playsInline
          />
        ) : (
          <img
            src={slide.file}
            alt={slide.title}
            className="w-full object-contain rounded-xl"
            style={{ maxHeight: '75vh', background: '#000' }}
          />
        )}
        <div style={{ marginTop: 20, textAlign: 'center' }}>
          <p
            className="font-semibold"
            style={{ fontSize: 18, marginBottom: 10 }}
          >
            {slide.title}
          </p>
          <div
            className="flex items-center justify-center"
            style={{ gap: 10 }}
          >
            <PlatformBadge platform={slide.platform} size="md" />
            <p
              className="text-muted font-mono"
              style={{ fontSize: 14 }}
            >
              {slide.desc}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
