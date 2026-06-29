import { Heart, MessageCircle, Send, Bookmark, MoreHorizontal, Smile } from 'lucide-react';

interface Props {
  imageSrc: string;
  slideNumber: number;
  totalSlides: number;
}

export function InstagramPhoneFrame({ imageSrc, slideNumber, totalSlides }: Props) {
  return (
    <div className="w-full h-full flex flex-col overflow-hidden text-left" style={{ background: '#fff', color: '#000' }}>
      {/* Status bar */}
      <div
        className="flex items-center justify-between"
        style={{ padding: '4px 16px', fontSize: 12, fontWeight: 600 }}
      >
        <span>9:41</span>
        <div className="flex items-center" style={{ gap: 4 }}>
          <svg width="16" height="12" viewBox="0 0 16 12" fill="#000">
            <rect x="0" y="8" width="3" height="4" rx="0.5" opacity="0.3"/>
            <rect x="4" y="5" width="3" height="7" rx="0.5" opacity="0.5"/>
            <rect x="8" y="2" width="3" height="10" rx="0.5" opacity="0.7"/>
            <rect x="12" y="0" width="3" height="12" rx="0.5"/>
          </svg>
          <svg width="16" height="12" viewBox="0 0 16 12" fill="#000">
            <path d="M8 3C10.7 3 13.1 4.2 14.7 6.1L16 4.8C14 2.5 11.2 1 8 1S2 2.5 0 4.8L1.3 6.1C2.9 4.2 5.3 3 8 3Z" opacity="0.3"/>
            <path d="M8 7C9.6 7 11 7.7 12 8.8L13.3 7.5C11.9 6 10.1 5 8 5S4.1 6 2.7 7.5L4 8.8C5 7.7 6.4 7 8 7Z" opacity="0.6"/>
            <circle cx="8" cy="11" r="1.5"/>
          </svg>
          <div className="w-6 h-3 rounded-sm border border-black relative">
            <div className="absolute rounded-sm bg-black" style={{ top: 1, left: 1, bottom: 1, width: '70%' }} />
          </div>
        </div>
      </div>

      {/* Instagram header */}
      <div
        className="flex items-center justify-between"
        style={{ padding: '6px 14px', borderBottom: '1px solid #efefef' }}
      >
        {/* Instagram logo text */}
        <span style={{ fontSize: 22, fontWeight: 400, fontFamily: 'Georgia, serif', fontStyle: 'italic' }}>Instagram</span>
        {/* Right icons */}
        <div className="flex items-center" style={{ gap: 18 }}>
          <Heart size={24} style={{ color: '#262626' }} />
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#262626" strokeWidth="1.5">
            <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
          </svg>
        </div>
      </div>

      {/* Stories bar */}
      <div
        className="flex"
        style={{ gap: 10, padding: '10px 12px', borderBottom: '1px solid #efefef' }}
      >
        {['Your story', 'sarah.r', 'mike_dev', 'lisa.t', 'james_w'].map((name, i) => (
          <div key={name} className="flex flex-col items-center flex-shrink-0" style={{ width: 56, gap: 3 }}>
            <div
              className="rounded-full flex items-center justify-center"
              style={{
                width: 50,
                height: 50,
                border: i === 0 ? '2px dashed #ccc' : '2.5px solid transparent',
                background: i === 0 ? 'transparent' : 'linear-gradient(#fff, #fff) padding-box, linear-gradient(135deg, #f59e0b, #ef4444, #ec4899, #8b5cf6) border-box',
                borderRadius: '50%',
                padding: 2,
              }}
            >
              {i === 0 ? (
                <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: '#ccc', color: '#fff', fontSize: 14, lineHeight: 1 }}>+</div>
                </div>
              ) : (
                <div className="w-full h-full rounded-full" style={{ background: 'linear-gradient(135deg, #f59e0b, #ef4444, #ec4899)' }} />
              )}
            </div>
            <span style={{ fontSize: 10, color: '#262626', textAlign: 'center', lineHeight: 1.2 }}>{name}</span>
          </div>
        ))}
      </div>

      {/* Scrollable post area */}
      <div className="flex-1 overflow-y-auto">
        {/* Post header */}
        <div className="flex items-center justify-between" style={{ padding: '10px 12px' }}>
          <div className="flex items-center" style={{ gap: 10 }}>
            <div
              className="rounded-full flex-shrink-0"
              style={{
                width: 34,
                height: 34,
                padding: 2,
                background: 'linear-gradient(135deg, #f59e0b, #ef4444, #ec4899)',
              }}
            >
              <div className="w-full h-full rounded-full" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)', border: '2px solid #fff' }} />
            </div>
            <div>
              <span style={{ fontSize: 13, fontWeight: 600 }}>realestate_ai</span>
              <span style={{ fontSize: 12, color: '#262626' }}> • </span>
              <span style={{ fontSize: 12, color: '#262626' }}>New York, NY</span>
            </div>
          </div>
          <MoreHorizontal size={20} style={{ color: '#262626' }} />
        </div>

        {/* Post image — the slide */}
        <div className="w-full bg-black relative" style={{ aspectRatio: '4/5' }}>
          <img src={imageSrc} alt="Slide" className="w-full h-full" style={{ objectFit: 'contain' }} />
          {/* Carousel dots */}
          <div
            className="absolute flex items-center justify-center"
            style={{ bottom: 10, left: 0, right: 0, gap: 4 }}
          >
            {Array.from({ length: totalSlides }).map((_, i) => (
              <div
                key={i}
                className="rounded-full"
                style={{
                  width: 6,
                  height: 6,
                  background: i + 1 === slideNumber ? '#0095f6' : 'rgba(255,255,255,0.5)',
                }}
              />
            ))}
          </div>
        </div>

        {/* Action buttons */}
        <div
          className="flex items-center justify-between"
          style={{ padding: '8px 12px' }}
        >
          <div className="flex items-center" style={{ gap: 16 }}>
            <Heart size={24} style={{ color: '#262626' }} />
            <MessageCircle size={24} style={{ color: '#262626' }} />
            <Send size={24} style={{ color: '#262626' }} />
          </div>
          <Bookmark size={24} style={{ color: '#262626' }} />
        </div>

        {/* Likes */}
        <div style={{ padding: '0 12px', fontSize: 13, fontWeight: 600 }}>
          1,247 likes
        </div>

        {/* Caption */}
        <div style={{ padding: '6px 12px', fontSize: 13 }}>
          <span style={{ fontWeight: 600 }}>realestate_ai</span>{' '}
          <span>NYC rents just jumped 14.2% — here's what the data says about where it's heading next.</span>
        </div>

        {/* Comments link */}
        <div style={{ padding: '0 12px', fontSize: 13, color: '#8e8e8e' }}>
          View all 89 comments
        </div>

        {/* Timestamp */}
        <div style={{ padding: '4px 12px', fontSize: 10, color: '#8e8e8e', textTransform: 'uppercase' }}>
          2 hours ago
        </div>

        {/* Add comment */}
        <div
          className="flex items-center justify-between"
          style={{ padding: '10px 12px', borderTop: '1px solid #efefef', marginTop: 8 }}
        >
          <div className="flex items-center" style={{ gap: 10 }}>
            <Smile size={22} style={{ color: '#8e8e8e' }} />
            <span style={{ fontSize: 13, color: '#8e8e8e' }}>Add a comment...</span>
          </div>
        </div>
      </div>
    </div>
  );
}
