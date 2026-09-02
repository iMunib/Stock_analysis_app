import React from "react";

export interface GridProps {
  children: React.ReactNode;
  cols?: 1 | 2 | 3 | 4 | 6 | 12;
  gap?: 2 | 3 | 4 | 6 | 8;
  className?: string;
}

const colClasses: Record<number, string> = {
  1: "grid-cols-1",
  2: "grid-cols-1 md:grid-cols-2",
  3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
  6: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6",
  12: "grid-cols-12",
};

const gapClasses: Record<number, string> = {
  2: "gap-2",
  3: "gap-3",
  4: "gap-4",
  6: "gap-6",
  8: "gap-8",
};

export function Grid({
  children,
  cols = 1,
  gap = 4,
  className = "",
}: GridProps) {
  const colClass = colClasses[cols] ?? "grid-cols-1";
  const gapClass = gapClasses[gap] ?? "gap-4";

  return (
    <div className={`grid ${colClass} ${gapClass} ${className}`}>
      {children}
    </div>
  );
}

export default Grid;
