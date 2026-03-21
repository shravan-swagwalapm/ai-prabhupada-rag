'use client';

export default function AratiDivider() {
  return (
    <div className="flex items-end justify-center gap-1 py-4" aria-hidden="true">
      {[0.7, 0.85, 1, 0.85, 0.7].map((scale, i) => (
        <div
          key={i}
          className="rounded-full"
          style={{
            width: `${4 * scale}px`,
            height: `${20 * scale}px`,
            background: 'linear-gradient(to top, #c24d2c, #c9a84c, #f7f0e3)',
            animation: `arati-flicker 2s ease-in-out infinite alternate`,
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
    </div>
  );
}
