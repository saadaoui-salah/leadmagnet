import { useState } from 'react';
import { ChevronLeft, ChevronRight, Smartphone } from 'lucide-react';
import { slides } from '../data/mockData';
import type { FilterTab } from '../data/types';
import { LinkedInPhoneFrame } from './LinkedInPhoneFrame';
import { InstagramPhoneFrame } from './InstagramPhoneFrame';

export function MobilePreview() {
  const [platform, setPlatform] = useState<FilterTab>('linkedin');
  const [currentIndex, setCurrentIndex] = useState(0);

  const filtered = slides.filter((s) => s.platform === platform);
  const currentSlide = filtered[currentIndex];

  const goNext = () => setCurrentIndex((i) => (i < filtered.length - 1 ? i + 1 : 0));
  const goPrev = () => setCurrentIndex((i) => (i > 0 ? i - 1 : filtered.length - 1));
  const goTo = (idx: number) => setCurrentIndex(idx);

  return (
    <div>
      {/* Section header + platform switcher */}
      <div className="flex items-center justify-between" style={{ marginBottom: 20 }}>
        <div className="flex items-center gap-2">
          <div className="w-1 h-5 rounded-full bg-secondary" />
          <Smartphone className="w-4 h-4 text-secondary" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Live Preview
          </h2>
        </div>

        {/* Platform tabs */}
        <div className="flex" style={{ gap: 10 }}>
          {(['linkedin', 'instagram'] as FilterTab[]).map((p) => (
            <button
              key={p}
              onClick={() => { setPlatform(p); setCurrentIndex(0); }}
              className={`rounded-lg text-sm font-medium border transition-all ${
                platform === p
                  ? p === 'linkedin'
                    ? 'bg-secondary/15 border-secondary/40 text-secondary'
                    : 'bg-pink-500/15 border-pink-400/40 text-pink-400'
                  : 'border-border text-muted hover:text-text'
              }`}
              style={{ padding: '6px 16px' }}
            >
              {p === 'linkedin' ? 'LinkedIn' : 'Instagram'}
            </button>
          ))}
        </div>
      </div>

      {/* Phone + thumbnails */}
      <div
        className="bg-surface/50 backdrop-blur-xl border border-border rounded-2xl"
        style={{ padding: '40px 32px 24px' }}
      >
        <div className="flex flex-col items-center">
          {/* Phone frame + arrows */}
          <div className="flex items-center" style={{ gap: 24 }}>
            {/* Prev arrow */}
            <button
              onClick={goPrev}
              className="rounded-full bg-surface border border-border text-muted hover:text-primary hover:border-primary/40 transition-all flex items-center justify-center flex-shrink-0"
              style={{ width: 40, height: 40 }}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            {/* Phone body — iPhone 15: 393x852 → ratio 1:2.17 */}
            <div
              className="relative flex-shrink-0"
              style={{ width: 300, height: 650 }}
            >
              {/* Outer shell */}
              <div
                className="absolute inset-0 border-[3px] border-[#3a3a5c] shadow-2xl overflow-hidden"
                style={{ background: 'linear-gradient(145deg, #1e1e32, #16162a)', borderRadius: 28 }}
              />

              {/* Side buttons */}
              <div className="absolute -left-[5px] top-[120px] w-[4px] h-[30px] bg-[#3a3a5c] rounded-l" />
              <div className="absolute -left-[5px] top-[170px] w-[4px] h-[30px] bg-[#3a3a5c] rounded-l" />
              <div className="absolute -right-[5px] top-[140px] w-[4px] h-[40px] bg-[#3a3a5c] rounded-r" />

              {/* Screen */}
              <div
                className="absolute overflow-hidden"
                style={{ top: 4, left: 4, right: 4, bottom: 4, borderRadius: 24 }}
              >
                {currentSlide && platform === 'linkedin' && (
                  <LinkedInPhoneFrame
                    imageSrc={currentSlide.file}
                    slideNumber={currentIndex + 1}
                    totalSlides={filtered.length}
                  />
                )}
                {currentSlide && platform === 'instagram' && (
                  <InstagramPhoneFrame
                    imageSrc={currentSlide.file}
                    slideNumber={currentIndex + 1}
                    totalSlides={filtered.length}
                  />
                )}
              </div>

              {/* Home indicator */}
              <div
                className="absolute left-1/2 -translate-x-1/2 bg-white/30 rounded-full z-30"
                style={{ bottom: 12, width: 100, height: 4 }}
              />
            </div>

            {/* Next arrow */}
            <button
              onClick={goNext}
              className="rounded-full bg-surface border border-border text-muted hover:text-primary hover:border-primary/40 transition-all flex items-center justify-center flex-shrink-0"
              style={{ width: 40, height: 40 }}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Slide counter */}
          <p className="text-sm text-muted font-mono" style={{ marginTop: 16 }}>
            {currentIndex + 1} / {filtered.length}
          </p>

          {/* Thumbnail strip */}
          <div
            className="flex overflow-x-auto"
            style={{ gap: 8, marginTop: 16, paddingBottom: 4, maxWidth: '100%' }}
          >
            {filtered.map((slide, idx) => (
              <button
                key={slide.id}
                onClick={() => goTo(idx)}
                className={`flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all bg-black ${
                  idx === currentIndex
                    ? 'border-primary shadow-[0_0_12px_rgba(43,238,52,0.3)]'
                    : 'border-border/50 opacity-60 hover:opacity-100'
                }`}
                style={{ width: 64, height: 80 }}
              >
                <img
                  src={slide.file}
                  alt={slide.title}
                  className="w-full h-full object-contain"
                />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
