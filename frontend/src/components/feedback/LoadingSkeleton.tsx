export interface LoadingSkeletonProps {
  lines?: number;
  height?: string;
  className?: string;
}

export function LoadingSkeleton({
  lines = 3,
  height = "h-4",
  className = "",
}: LoadingSkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Loading content..."
      className={`space-y-3 w-full animate-pulse-subtle ${className}`}
    >
      {Array.from({ length: lines }).map((_, idx) => (
        <div
          key={idx}
          className={`${height} rounded-chip animate-shimmer ${
            idx === lines - 1 && lines > 1 ? "w-3/4" : "w-full"
          }`}
        />
      ))}
      <span className="sr-only">Loading content…</span>
    </div>
  );
}

export default LoadingSkeleton;
