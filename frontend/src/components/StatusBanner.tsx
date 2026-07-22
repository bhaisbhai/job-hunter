import type { RunStatus } from "../types";

const STAGE_LABEL: Record<string, string> = {
  pending: "Queued…",
  scraping: "Scraping job sites…",
  evaluating: "Evaluating listings with Gemini…",
};

interface Props {
  status: RunStatus;
  errorMessage?: string | null;
}

export function StatusBanner({ status, errorMessage }: Props) {
  if (status === "failed") {
    return (
      <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
        <p className="font-semibold">The last run failed.</p>
        {errorMessage && (
          <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-xs text-rose-300/80">
            {errorMessage}
          </pre>
        )}
      </div>
    );
  }

  if (status === "completed") return null;

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-indigo-400/30 bg-indigo-500/10 px-5 py-4 text-sm text-indigo-200">
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-indigo-400" />
      </span>
      {STAGE_LABEL[status] ?? "Working…"}
    </div>
  );
}
