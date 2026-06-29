import { ThumbsUp, MessageCircle, Send, Bookmark, MoreHorizontal } from 'lucide-react';

interface Props {
  imageSrc: string;
  slideNumber: number;
  totalSlides: number;
}

export function LinkedInPhoneFrame({ imageSrc, slideNumber, totalSlides }: Props) {
  return (
    <div className="w-full h-full flex flex-col overflow-hidden text-left" style={{ background: '#f4f2ee', color: '#000' }}>
      {/* Status bar */}
      <div
        className="flex items-center justify-between"
        style={{ padding: '4px 20px', fontSize: 13, fontWeight: 600, height: 28 }}
      >
        <span>9:41</span>
        {/* Dynamic Island */}
        <div
          className="absolute left-1/2 -translate-x-1/2"
          style={{ top: 4, width: 80, height: 22, background: '#000', borderRadius: 20 }}
        />
        <div className="flex items-center" style={{ gap: 5 }}>
          {/* Signal bars */}
          <div className="flex items-end" style={{ gap: 1.5 }}>
            <div style={{ width: 3, height: 4, background: '#000', borderRadius: 1 }} />
            <div style={{ width: 3, height: 6, background: '#000', borderRadius: 1 }} />
            <div style={{ width: 3, height: 8, background: '#000', borderRadius: 1 }} />
            <div style={{ width: 3, height: 10, background: '#000', borderRadius: 1 }} />
          </div>
          {/* WiFi */}
          <svg width="14" height="10" viewBox="0 0 14 10" fill="#000">
            <path d="M7 8.5a1.2 1.2 0 110 2.4 1.2 1.2 0 010-2.4z" transform="translate(0,-2)"/>
            <path d="M4.5 7.5C5.1 6.9 6 6.5 7 6.5s1.9.4 2.5 1" fill="none" stroke="#000" strokeWidth="1.3" strokeLinecap="round"/>
            <path d="M2.5 5.5C3.5 4.5 5.2 3.8 7 3.8s3.5.7 4.5 1.7" fill="none" stroke="#000" strokeWidth="1.3" strokeLinecap="round"/>
            <path d="M0.5 3.2C2 1.8 4.4.8 7 .8s5 1 6.5 2.4" fill="none" stroke="#000" strokeWidth="1.3" strokeLinecap="round"/>
          </svg>
          {/* Battery */}
          <div className="flex items-center" style={{ gap: 1 }}>
            <div style={{ width: 22, height: 11, border: '1.5px solid #000', borderRadius: 3, padding: 1.5 }}>
              <div style={{ width: '75%', height: '100%', background: '#000', borderRadius: 1.5 }} />
            </div>
          </div>
        </div>
      </div>

      {/* LinkedIn nav header */}
      <div
        className="flex items-center justify-between relative"
        style={{ padding: '8px 14px', background: '#f4f2ee' }}
      >
        {/* LinkedIn logo */}
        <svg width="30" height="30" viewBox="0 0 24 24" fill="#0a66c2">
          <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.3 6.5a1.78 1.78 0 01-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0013 14.19a.66.66 0 000 .14V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.86 3.36 3.66z" />
        </svg>
        {/* Right icons */}
        <div className="flex items-center" style={{ gap: 18 }}>
          {/* Grid */}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="1.8">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          {/* Connections */}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="1.8">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          {/* Mail */}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="1.8">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
          {/* Profile */}
          <div className="w-8 h-8 rounded-full" style={{ background: 'linear-gradient(135deg, #0a66c2, #004182)' }} />
        </div>
      </div>

      {/* Stories bar */}
      <div
        className="flex"
        style={{ gap: 12, padding: '12px 14px', borderBottom: '1px solid #e0ddd9' }}
      >
        {['Your story', 'Sarah K.', 'Mike R.', 'Lisa T.', 'James W.'].map((name, i) => (
          <div key={name} className="flex flex-col items-center flex-shrink-0" style={{ width: 56, gap: 4 }}>
            <div
              className="rounded-full flex items-center justify-center"
              style={{
                width: 50,
                height: 50,
                border: i === 0 ? '2px dashed #0a66c2' : '2.5px solid transparent',
                background: i === 0 ? 'transparent' : 'linear-gradient(#f4f2ee, #f4f2ee) padding-box, linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7) border-box',
                borderRadius: '50%',
              }}
            >
              {i === 0 ? (
                <div className="w-full h-full rounded-full flex items-center justify-center" style={{ background: '#fff' }}>
                  <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: '#0a66c2', color: '#fff', fontSize: 16, fontWeight: 400, lineHeight: 1 }}>+</div>
                </div>
              ) : (
                <div className="w-full h-full rounded-full" style={{ background: 'linear-gradient(135deg, #818cf8, #a78bfa, #c084fc)' }} />
              )}
            </div>
            <span style={{ fontSize: 10, color: '#666', textAlign: 'center', lineHeight: 1.2 }}>{name}</span>
          </div>
        ))}
      </div>

      {/* Scrollable post area */}
      <div className="flex-1 overflow-y-auto">
        {/* Post header */}
        <div className="flex items-center" style={{ padding: '10px 12px', gap: 8 }}>
          <div className="w-10 h-10 rounded-full flex-shrink-0" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center" style={{ gap: 4 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#000', whiteSpace: 'nowrap' }}>Real Estate Intelligence</span>
              <span style={{ fontSize: 11, color: '#999', whiteSpace: 'nowrap' }}>• 2h</span>
            </div>
            <span style={{ fontSize: 11, color: '#666', whiteSpace: 'nowrap' }}>Market Analyst • New York, NY</span>
          </div>
          <MoreHorizontal size={18} style={{ color: '#666', flexShrink: 0 }} />
        </div>

        {/* Post image — the slide */}
        <div className="w-full bg-black relative" style={{ aspectRatio: '4/5' }}>
          <img src={imageSrc} alt="Slide" className="w-full h-full" style={{ objectFit: 'contain' }} />
          {/* Slide counter */}
          <div
            className="absolute"
            style={{ top: 10, right: 10, background: 'rgba(0,0,0,0.6)', color: '#fff', padding: '3px 8px', borderRadius: 4, fontSize: 10 }}
          >
            {slideNumber}/{totalSlides}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-between" style={{ padding: '10px 14px' }}>
          <div className="flex items-center" style={{ gap: 18 }}>
            <ThumbsUp size={22} style={{ color: '#666' }} />
            <MessageCircle size={22} style={{ color: '#666' }} />
            <Send size={22} style={{ color: '#666' }} />
          </div>
          <Bookmark size={22} style={{ color: '#666' }} />
        </div>

        {/* Likes */}
        <div className="flex items-center" style={{ padding: '0 14px', gap: 5, fontSize: 13, color: '#333' }}>
          <div className="flex">
            <div className="w-4 h-4 rounded-full" style={{ background: '#3b82f6', border: '1.5px solid #fff' }} />
            <div className="w-4 h-4 rounded-full" style={{ background: '#22c55e', border: '1.5px solid #fff', marginLeft: -4 }} />
            <div className="w-4 h-4 rounded-full" style={{ background: '#ef4444', border: '1.5px solid #fff', marginLeft: -4 }} />
          </div>
          <span style={{ fontWeight: 600 }}>247 likes</span>
        </div>

        {/* Caption */}
        <div style={{ padding: '8px 14px', fontSize: 13 }}>
          <span style={{ fontWeight: 600 }}>realestate_ai</span>{' '}
          <span style={{ color: '#333' }}>NYC rents just jumped 14.2% — here's what the data says about where it's heading next.</span>
        </div>

        {/* Comments link */}
        <div style={{ padding: '0 14px', fontSize: 13, color: '#999' }}>
          View all 34 comments
        </div>

        {/* Add comment */}
        <div
          className="flex items-center"
          style={{ padding: '12px 14px', gap: 10, borderTop: '1px solid #e0ddd9', marginTop: 10 }}
        >
          <div className="w-8 h-8 rounded-full flex-shrink-0" style={{ background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' }} />
          <span style={{ fontSize: 13, color: '#999' }}>Add a comment...</span>
        </div>
      </div>
    </div>
  );
}
