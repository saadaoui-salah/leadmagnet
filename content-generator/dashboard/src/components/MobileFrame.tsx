import { ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  slides: { file: string; title: string; platform: string }[];
  currentIndex: number;
  onPrev: () => void;
  onNext: () => void;
  label: string;
}

export function MobileFrame({ slides, currentIndex, onPrev, onNext, label }: Props) {
  const slide = slides[currentIndex];

  return (
    <div className="flex flex-col items-center">
      {/* Label */}
      <p className="text-xs text-muted uppercase tracking-wider font-medium mb-4">{label}</p>

      {/* Phone + Arrows wrapper */}
      <div className="flex items-center gap-4">
        {/* Prev */}
        <button
          onClick={onPrev}
          className="p-2 rounded-full bg-surface border border-border text-muted hover:text-primary hover:border-primary/40 transition-all flex-shrink-0"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>

        {/* Phone body — iPhone-style with proper 4:5 ratio */}
        <div
          className="relative flex-shrink-0"
          style={{ width: 280, height: 560 }}
        >
          {/* Outer frame */}
          <div className="absolute inset-0 bg-[#1c1c2e] rounded-[40px] border-[3px] border-[#3a3a5c] shadow-2xl" />

          {/* Notch / Dynamic Island */}
          <div className="absolute top-[6px] left-1/2 -translate-x-1/2 w-20 h-[22px] bg-[#1c1c2e] rounded-full z-20" />

          {/* Screen area */}
          <div
            className="absolute overflow-hidden rounded-[36px]"
            style={{ top: 3, left: 3, right: 3, bottom: 3 }}
          >
            {slide ? (
              <img
                src={slide.file}
                alt={slide.title}
                className="w-full h-full"
                style={{ objectFit: 'contain', background: '#000' }}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-muted text-xs bg-black">
                No slides
              </div>
            )}
          </div>

          {/* Home indicator */}
          <div className="absolute bottom-[10px] left-1/2 -translate-x-1/2 w-28 h-[4px] bg-white/20 rounded-full z-20" />
        </div>

        {/* Next */}
        <button
          onClick={onNext}
          className="p-2 rounded-full bg-surface border border-border text-muted hover:text-primary hover:border-primary/40 transition-all flex-shrink-0"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Counter */}
      <p className="text-xs text-muted font-mono mt-3">
        {currentIndex + 1} / {slides.length}
      </p>
    </div>
  );
}
