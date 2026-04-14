'use client';
import { useState } from 'react';

interface ShareBarProps {
  answerText: string;
  question: string;
}

function formatForShare(question: string, answer: string): string {
  const clean = answer
    .replace(/#{1,3}\s/g, '')
    .replace(/\*\*/g, '')
    .replace(/^\s*[-•]\s/gm, '• ')
    .trim();
  return `Q: ${question}\n\n${clean.slice(0, 500)}...\n\n— Prabhupada AI`;
}

export default function ShareBar({ answerText, question }: ShareBarProps) {
  const [copied, setCopied] = useState(false);
  const formatted = formatForShare(question, answerText);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable (non-HTTPS or unfocused document)
    }
  };

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({ title: 'Prabhupada AI', text: formatted });
      } else {
        await handleCopy();
      }
    } catch {
      // User cancelled share dialog or permission denied
    }
  };

  const handleTweet = () => {
    const text = encodeURIComponent(formatted.slice(0, 250) + '...');
    window.open(`https://x.com/intent/tweet?text=${text}`, '_blank');
  };

  return (
    <div className="flex gap-3 py-3 px-4 border-t"
         style={{ borderColor: 'var(--glass-border)', background: 'var(--glass)', backdropFilter: 'blur(12px)' }}>
      <button onClick={handleCopy} className="font-display text-sm tracking-wider px-4 py-2 min-h-[44px] rounded-full border transition-colors"
              style={{ borderColor: 'var(--glass-border-hover)', color: copied ? 'var(--tulsi)' : 'var(--text-secondary)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--card-hover)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = ''; }}>
        {copied ? 'Copied ✓' : 'Copy'}
      </button>
      <button onClick={handleShare} className="font-display text-sm tracking-wider px-4 py-2 min-h-[44px] rounded-full border transition-colors"
              style={{ borderColor: 'var(--glass-border-hover)', color: 'var(--text-secondary)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--card-hover)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = ''; }}>
        Share
      </button>
      <button onClick={handleTweet} className="font-display text-sm tracking-wider px-4 py-2 min-h-[44px] rounded-full border transition-colors"
              style={{ borderColor: 'var(--glass-border-hover)', color: 'var(--text-secondary)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--card-hover)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = ''; }}>
        Tweet
      </button>
    </div>
  );
}
