interface Props {
  score: number;
}

function toneFor(score: number): string {
  if (score >= 9) return "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30";
  if (score >= 7) return "bg-teal-500/15 text-teal-300 ring-teal-500/30";
  if (score >= 5) return "bg-amber-500/15 text-amber-300 ring-amber-500/30";
  return "bg-rose-500/15 text-rose-300 ring-rose-500/30";
}

export function ScoreBadge({ score }: Props) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-sm font-semibold ring-1 ring-inset ${toneFor(score)}`}
    >
      {score}
      <span className="text-xs font-normal opacity-70">/10</span>
    </span>
  );
}
