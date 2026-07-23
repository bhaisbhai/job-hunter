import type { Run } from "../types";

const STAGE_LABEL: Record<string, string> = {
  pending: "Queued…",
  scraping: "Scraping job sites…",
  evaluating: "Evaluating listings with Gemini…",
};

interface Props {
  run: Run;
}

export function StatusBanner({ run }: Props) {
  const { status, error_message, listings_scraped, evaluated_count, evaluation_failures } = run;

  if (status === "failed") {
    return (
      <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
        <p className="font-semibold">The last run failed.</p>
        {evaluated_count > 0 && (
          <p className="mt-1 text-rose-300/80">
            {evaluated_count} listing(s) were evaluated before it failed — results below are still saved.
          </p>
        )}
        {error_message && (
          <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-xs text-rose-300/80">
            {error_message}
          </pre>
        )}
      </div>
    );
  }

  if (status === "completed") return null;

  const done = evaluated_count + evaluation_failures;
  const showProgress = status === "evaluating" && listings_scraped > 0;

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-indigo-400/30 bg-indigo-500/10 px-5 py-4 text-sm text-indigo-200">
      <span className="relative flex h-2.5 w-2.5 shrink-0">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-indigo-400" />
      </span>
      <span>
        {STAGE_LABEL[status] ?? "Working…"}
        {showProgress && (
          <span className="ml-1.5 text-indigo-300/80">
            ({done}/{listings_scraped}
            {evaluation_failures > 0 ? `, ${evaluation_failures} failed` : ""})
          </span>
        )}
      </span>
    </div>
  );
}
