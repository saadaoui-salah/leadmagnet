import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { LayoutGrid, List, Monitor, Play, Loader2, CheckCircle2, XCircle, Send } from 'lucide-react';
import { slides } from '../data/mockData';
import type { FilterTab } from '../data/types';
import { MarketStats } from './MarketStats';
import { FilterBar } from './FilterBar';
import { SlideCard } from './SlideCard';
import { Lightbox } from './Lightbox';
import { MobilePreview } from './MobilePreview';
import { PlatformBadge, SlideNumber } from './PlatformBadge';

interface GenStatus {
  running: boolean
  step: string
  progress: number
  error: string | null
  lastRun: string | null
}

export function Dashboard({ onNavigate }: { onNavigate: () => void }) {
  const [filter, setFilter] = useState<FilterTab>('all');
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null);
  const [genStatus, setGenStatus] = useState<GenStatus | null>(null);
  const wasRunning = useRef(false);

  const pollStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status')
      const data = await res.json()
      setGenStatus(data)
    } catch {}
  }, [])

  useEffect(() => {
    pollStatus()
    const iv = setInterval(pollStatus, 2000)
    return () => clearInterval(iv)
  }, [pollStatus])

  // Auto-reload when generation finishes
  useEffect(() => {
    if (wasRunning.current && !genStatus?.running) {
      window.location.reload()
    }
    wasRunning.current = !!genStatus?.running
  }, [genStatus?.running])

  const handleGenerate = async () => {
    try {
      await fetch('/api/generate', { method: 'POST' })
      pollStatus()
    } catch (err) {
      console.error('Failed to start generation:', err)
    }
  }

  const filtered = useMemo(
    () => (filter === 'all' ? slides : slides.filter((s) => s.platform === filter)),
    [filter]
  );

  const counts = useMemo(
    () => ({
      all: slides.length,
      linkedin: slides.filter((s) => s.platform === 'linkedin').length,
      instagram: slides.filter((s) => s.platform === 'instagram').length,
      youtube: slides.filter((s) => s.platform === 'youtube').length,
      facebook: slides.filter((s) => s.platform === 'facebook').length,
      threads: slides.filter((s) => s.platform === 'threads').length,
      x: slides.filter((s) => s.platform === 'x').length,
    }),
    []
  );

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header
        className="sticky top-0 z-40 bg-bg/80 backdrop-blur-xl border-b border-border/50"
        style={{ paddingLeft: 48, paddingRight: 48 }}
      >
        <div
          className="flex items-center justify-between"
          style={{ maxWidth: 1400, margin: '0 auto', height: 56 }}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Monitor className="w-4 h-4 text-bg" />
            </div>
            <h1 className="text-lg font-bold">Content Dashboard</h1>
            <span className="text-xs text-muted bg-surface px-2 py-0.5 rounded font-mono">
              v1.0
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted">
            <span>2026-06-24</span>
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            <button
              onClick={onNavigate}
              className="flex items-center gap-2 rounded-lg font-semibold transition-all"
              style={{
                padding: '7px 16px',
                fontSize: 13,
                background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                color: '#fff',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              <Send size={14} />
              Buffer Upload
            </button>
            <button
              onClick={handleGenerate}
              disabled={genStatus?.running}
              className="flex items-center gap-2 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                padding: '7px 16px',
                fontSize: 13,
                background: genStatus?.running ? '#1e293b' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                border: 'none',
                cursor: genStatus?.running ? 'not-allowed' : 'pointer',
              }}
            >
              {genStatus?.running ? (
                <Loader2 size={14} className="animate-spin" />
              ) : genStatus?.error ? (
                <XCircle size={14} />
              ) : genStatus?.lastRun ? (
                <CheckCircle2 size={14} />
              ) : (
                <Play size={14} />
              )}
              {genStatus?.running ? genStatus.step : genStatus?.lastRun ? 'Regenerate' : 'Generate Report'}
            </button>
          </div>
        </div>
      </header>

      {/* Generation progress bar */}
      {genStatus?.running && (
        <div style={{ background: '#0f172a', borderBottom: '1px solid rgba(99,102,241,0.2)' }}>
          <div
            style={{
              maxWidth: 1400,
              margin: '0 auto',
              padding: '10px 48px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <Loader2 size={14} className="animate-spin" style={{ color: '#818cf8' }} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: '#94a3b8' }}>{genStatus.step}</span>
                <span style={{ fontSize: 12, color: '#6366f1', fontWeight: 600 }}>{genStatus.progress}%</span>
              </div>
              <div style={{ height: 4, background: '#1e293b', borderRadius: 2, overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${genStatus.progress}%`,
                    background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                    borderRadius: 2,
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Generation error */}
      {genStatus?.error && !genStatus.running && (
        <div style={{ background: 'rgba(239,68,68,0.1)', borderBottom: '1px solid rgba(239,68,68,0.2)' }}>
          <div
            style={{
              maxWidth: 1400,
              margin: '0 auto',
              padding: '10px 48px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <XCircle size={14} style={{ color: '#ef4444' }} />
            <span style={{ fontSize: 12, color: '#fca5a5' }}>{genStatus.error}</span>
          </div>
        </div>
      )}

      {/* Main content */}
      <div style={{ paddingLeft: 48, paddingRight: 48 }}>
        <main
          style={{ maxWidth: 1400, margin: '0 auto', paddingBottom: 60, paddingTop: 32 }}
        >
          {/* Market Stats */}
          <section style={{ marginBottom: 40 }}>
            <MarketStats />
          </section>

          {/* Mobile Preview */}
          <section style={{ marginBottom: 40 }}>
            <MobilePreview />
          </section>

          {/* Slides Section */}
          <section>
            {/* Section header */}
            <div className="flex items-center justify-between flex-wrap gap-4" style={{ marginBottom: 20 }}>
              <div className="flex items-center gap-2">
                <div className="w-1 h-5 rounded-full bg-primary" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
                  Generated Slides
                </h2>
              </div>
              <div className="flex items-center" style={{ gap: 12 }}>
                <FilterBar active={filter} onChange={setFilter} counts={counts} />
                <div className="flex" style={{ gap: 4 }}>
                  <button
                    onClick={() => setView('grid')}
                    className={`rounded-lg border transition-all flex items-center justify-center ${
                      view === 'grid'
                        ? 'border-primary/30 text-primary'
                        : 'border-border text-muted'
                    }`}
                    style={{ padding: '6px 8px' }}
                  >
                    <LayoutGrid className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setView('list')}
                    className={`rounded-lg border transition-all flex items-center justify-center ${
                      view === 'list'
                        ? 'border-primary/30 text-primary'
                        : 'border-border text-muted'
                    }`}
                    style={{ padding: '6px 8px' }}
                  >
                    <List className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Grid View */}
            {view === 'grid' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14 }}>
                {filtered.map((slide) => (
                  <SlideCard
                    key={slide.id}
                    slide={slide}
                    onClick={() => setLightboxIdx(slides.indexOf(slide))}
                  />
                ))}
              </div>
            )}

            {/* List View */}
            {view === 'list' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {filtered.map((slide) => (
                    <button
                      key={slide.id}
                      onClick={() => setLightboxIdx(slides.indexOf(slide))}
                      className="w-full bg-surface/80 backdrop-blur-xl border border-border rounded-xl flex items-center text-left hover:border-primary/30 transition-all cursor-pointer overflow-hidden"
                      style={{ padding: '10px 14px', gap: 14 }}
                    >
                      <img
                        src={slide.file}
                        alt={slide.title}
                        className="object-contain rounded-lg flex-shrink-0 bg-black"
                        style={{ width: 56, height: 70 }}
                        loading="lazy"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center" style={{ gap: 10, marginBottom: 4 }}>
                          <PlatformBadge platform={slide.platform} />
                          <SlideNumber id={slide.id} />
                        </div>
                        <p className="text-sm font-semibold text-text truncate">{slide.title}</p>
                        <p className="text-xs text-muted truncate">{slide.desc}</p>
                      </div>
                    </button>
                ))}
              </div>
            )}
          </section>
        </main>
      </div>

      {/* Lightbox */}
      {lightboxIdx !== null && (
        <Lightbox
          slides={slides}
          currentIndex={lightboxIdx}
          onClose={() => setLightboxIdx(null)}
          onPrev={() => setLightboxIdx((i) => (i !== null && i > 0 ? i - 1 : slides.length - 1))}
          onNext={() => setLightboxIdx((i) => (i !== null && i < slides.length - 1 ? i + 1 : 0))}
        />
      )}
    </div>
  );
}
