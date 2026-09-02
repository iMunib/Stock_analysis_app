import { useEffect, useRef, useState } from "react";

/**
 * useCountUp: Animates a numeric counter smoothly over duration ms using requestAnimationFrame.
 * Strictly checks `prefers-reduced-motion: reduce` and immediately snaps to target without animating.
 */
export function useCountUp(
  targetValue: number | null | undefined,
  duration = 400,
  decimals = 1
): number | null {
  const [displayValue, setDisplayValue] = useState<number | null>(() => {
    if (targetValue === null || targetValue === undefined || isNaN(targetValue)) {
      return null;
    }
    return targetValue;
  });

  const prevTargetRef = useRef<number | null>(targetValue ?? null);

  useEffect(() => {
    if (targetValue === null || targetValue === undefined || isNaN(targetValue)) {
      setDisplayValue(null);
      prevTargetRef.current = null;
      return;
    }

    // Check if user prefers reduced motion
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReduced) {
      setDisplayValue(targetValue);
      prevTargetRef.current = targetValue;
      return;
    }

    const startVal = prevTargetRef.current ?? 0;
    const endVal = targetValue;
    prevTargetRef.current = endVal;

    if (startVal === endVal) {
      setDisplayValue(endVal);
      return;
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic: 1 - (1 - t)^3
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = startVal + (endVal - startVal) * easeOut;

      const factor = Math.pow(10, decimals);
      setDisplayValue(Math.round(current * factor) / factor);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step);
      } else {
        setDisplayValue(endVal);
      }
    };

    animationFrameId = requestAnimationFrame(step);

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [targetValue, duration, decimals]);

  return displayValue;
}

export default useCountUp;
