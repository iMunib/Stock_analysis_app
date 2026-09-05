export type VerdictTone = "positive" | "warning" | "negative" | "info";

export interface VerdictBadgeProps {
  verdict?: string;
  tone?: VerdictTone;
  confidence?: string;
  pillarsComplete?: number;
  className?: string;
}

export function computeVerdict(params: {
  signal?: string | null;
  moatPass?: boolean;
  altmanSafe?: boolean;
  altmanDistress?: boolean;
  reverseDcfGap?: number | null; // e.g. -2, +5, etc.
  beneishFlagged?: boolean;
  isCyclical?: boolean;
  peRatio?: number | null;
  coverage?: number | null;
}): { label: string; tone: VerdictTone; confidence: string } {
  const {
    signal,
    moatPass = false,
    altmanSafe = false,
    altmanDistress = false,
    reverseDcfGap = null,
    beneishFlagged = false,
    isCyclical = false,
    peRatio = null,
    coverage = 4,
  } = params;

  const conf =
    coverage && coverage >= 4
      ? "HIGH (4/4 Pillars Complete)"
      : coverage === 3
      ? "MEDIUM (3/4 Pillars Complete)"
      : "PRELIMINARY (Partial Coverage)";

  // 1. Red: Distress / Value Trap / Accounting Manipulation
  if (altmanDistress || beneishFlagged || signal === "avoid") {
    return {
      label: "AVOID: VALUE TRAP / DISTRESS",
      tone: "negative",
      confidence: conf,
    };
  }

  // 2. Amber: Cyclical Peak Caution
  if (isCyclical && peRatio && peRatio < 12) {
    return {
      label: "CYCLICAL PEAK: CAUTION",
      tone: "warning",
      confidence: conf,
    };
  }

  // 3. Amber: Overvalued Quality (Priced for perfection)
  if (moatPass && reverseDcfGap !== null && reverseDcfGap > 6) {
    return {
      label: "OVERVALUED QUALITY",
      tone: "warning",
      confidence: conf,
    };
  }

  // 4. Green: Undervalued Bargain
  if (altmanSafe && !beneishFlagged && (signal === "strong_candidate" || (reverseDcfGap !== null && reverseDcfGap < -3))) {
    return {
      label: "UNDERVALUED BARGAIN",
      tone: "positive",
      confidence: conf,
    };
  }

  // 5. Green: Compounder at Fair Value
  if (moatPass && altmanSafe && (reverseDcfGap === null || reverseDcfGap <= 3)) {
    return {
      label: "COMPOUNDER AT FAIR VALUE",
      tone: "positive",
      confidence: conf,
    };
  }

  // 6. Signal-based fallback
  if (signal === "strong_candidate" || signal === "constructive") {
    return {
      label: "COMPOUNDER AT FAIR VALUE",
      tone: "positive",
      confidence: conf,
    };
  }

  if (signal === "mixed") {
    return {
      label: "FAIR VALUE QUALITY",
      tone: "warning",
      confidence: conf,
    };
  }

  return {
    label: "BALANCED RESEARCH PROFILE",
    tone: "info",
    confidence: conf,
  };
}

export function VerdictBadge({
  verdict = "COMPOUNDER AT FAIR VALUE",
  tone = "positive",
  confidence = "HIGH (4/4 Pillars Complete)",
  className = "",
}: VerdictBadgeProps) {
  const toneClasses: Record<VerdictTone, { pill: string; dot: string; text: string }> = {
    positive: {
      pill: "bg-pos-weak border-pos/40 text-pos",
      dot: "bg-pos",
      text: "text-pos",
    },
    warning: {
      pill: "bg-warn-weak border-warn/40 text-warn",
      dot: "bg-warn",
      text: "text-warn",
    },
    negative: {
      pill: "bg-neg-weak border-neg/40 text-neg",
      dot: "bg-neg",
      text: "text-neg",
    },
    info: {
      pill: "bg-info-weak border-info/40 text-info",
      dot: "bg-info",
      text: "text-info",
    },
  };

  const current = toneClasses[tone] || toneClasses.positive;

  return (
    <div className={`flex flex-wrap items-center gap-3 ${className}`}>
      <span
        className={`inline-flex items-center gap-2 rounded-card border px-3.5 py-1.5 font-mono text-xs sm:text-sm font-bold tracking-wide shadow-xs ${current.pill}`}
      >
        <span className={`h-2 w-2 rounded-full ${current.dot} animate-pulse-subtle`} aria-hidden="true" />
        <span>{verdict}</span>
      </span>
      {confidence && (
        <span className="font-mono text-xs text-ink-1 flex items-center gap-1.5">
          <span className="text-ink-2">•</span>
          <span>Confidence: <strong className="text-ink-0 font-semibold">{confidence}</strong></span>
        </span>
      )}
    </div>
  );
}

export default VerdictBadge;
