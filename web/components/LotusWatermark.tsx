"use client";

export default function LotusWatermark() {
  return (
    <div
      className="absolute inset-0 flex items-center justify-center pointer-events-none"
      aria-hidden="true"
    >
      <svg
        width="280"
        height="280"
        viewBox="0 0 200 200"
        style={{ opacity: 0.02 }}
      >
        {Array.from({ length: 8 }).map((_, i) => (
          <ellipse
            key={i}
            cx="100"
            cy="100"
            rx="16"
            ry="38"
            fill="#C9A84C"
            transform={`rotate(${i * 45} 100 100)`}
          />
        ))}
        <circle cx="100" cy="100" r="8" fill="#C9A84C" />
      </svg>
    </div>
  );
}
