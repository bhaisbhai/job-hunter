import type { Run } from "../types";

interface Props {
  runs: Run[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function RunSelector({ runs, selectedRunId, onSelect }: Props) {
  if (runs.length === 0) return null;

  return (
    <select
      value={selectedRunId ?? ""}
      onChange={(e) => onSelect(e.target.value)}
      className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 outline-none transition focus:border-indigo-400/50"
    >
      {runs.map((run) => (
        <option key={run.id} value={run.id} className="bg-slate-900">
          {formatDate(run.started_at)} — {run.status}
          {run.status === "completed" ? ` (${run.matched_count} match${run.matched_count === 1 ? "" : "es"})` : ""}
        </option>
      ))}
    </select>
  );
}
