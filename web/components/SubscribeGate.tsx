'use client';
import { useState, useEffect, useRef } from 'react';
import { submitWaitlist } from '@/lib/api';
import AratiDivider from './AratiDivider';

interface SubscribeGateProps {
  quotaType: 'text' | 'voice';
  userEmail: string;
  textUsed: number;
  voiceUsed: number;
  onSubmit: (email: string) => void;
  onDismiss: () => void;
}

export default function SubscribeGate({ quotaType, userEmail, textUsed, voiceUsed, onSubmit, onDismiss }: SubscribeGateProps) {
  const [email, setEmail] = useState(userEmail);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const dialogRef = useRef<HTMLDivElement>(null);

  // Escape key to dismiss + focus trap
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss();
    };
    document.addEventListener('keydown', handleKeyDown);
    // Focus the dialog on mount
    dialogRef.current?.focus();
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onDismiss]);

  const handleSubmit = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email');
      return;
    }
    try {
      await submitWaitlist(email);
      setSubmitted(true);
      onSubmit(email);
    } catch {
      setError('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(6,4,3,0.85)' }} onClick={onDismiss}>
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Quota exhausted"
        tabIndex={-1}
        className="max-w-md w-full rounded-2xl p-8 text-center outline-none"
        style={{ background: 'var(--card)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <AratiDivider />
        <h2 className="font-serif text-2xl font-semibold mt-4" style={{ color: 'var(--text-primary)' }}>
          You've tasted the nectar
        </h2>
        <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
          You've asked {textUsed} question{textUsed !== 1 ? 's' : ''} and received {voiceUsed} voice answer{voiceUsed !== 1 ? 's' : ''}.
        </p>
        <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
          Unlock unlimited access to Prabhupada's wisdom
        </p>

        {submitted ? (
          <p className="mt-6 text-sm" style={{ color: 'var(--tulsi)' }}>
            We'll notify you when unlimited access is available.
          </p>
        ) : (
          <div className="mt-6 space-y-3">
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="w-full px-4 py-3 rounded-lg text-sm bg-transparent border outline-none focus:ring-2"
              style={{ borderColor: 'var(--glass-border-hover)', color: 'var(--text-body)', outlineColor: 'var(--gold)' }}
            />
            {error && <p className="text-sm" style={{ color: '#e07050' }}>{error}</p>}
            <button onClick={handleSubmit}
                    className="w-full py-3 rounded-lg font-display text-sm tracking-wider transition-colors"
                    style={{ background: 'var(--gold)', color: 'var(--sanctum)', minHeight: 44 }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--gold-bright)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--gold)'; }}>
              Join Waitlist ✦
            </button>
          </div>
        )}

        <button
          onClick={onDismiss}
          className="mt-4 text-sm px-4 transition-colors"
          style={{ color: 'var(--text-ghost)', minHeight: 44 }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-ghost)'; }}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
