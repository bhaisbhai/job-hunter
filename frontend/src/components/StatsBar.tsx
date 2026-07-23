import type { Run } from "../types";

interface Props {
  run: Run;
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | string;
  tone?: "warn";
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span
        className={`text-xl font-semibold ${tone === "warn" ? "text-amber-300" : "text-slate-100"}`}
      >
        {value}
      </span>
      <span className="text-xs text-slate-500">{label}</span>
    </div>
  );
}

export function StatsBar({ run }: Props) {
  return (
    <div className="flex flex-wrap gap-x-8 gap-y-3 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4">
      <Stat label="Listings scraped" value={run.listings_scraped} />
      <Stat label="Evaluated" value={run.evaluated_count} />
      {run.evaluation_failures > 0 && (
        <Stat label="Evaluation failed" value={run.evaluation_failures} tone="warn" />
      )}
      <Stat label="Matched (≥ threshold)" value={run.matched_count} />
      <Stat label="Digest emailed" value={run.email_sent ? "Yes" : "No"} />
    </div>
  );
}
