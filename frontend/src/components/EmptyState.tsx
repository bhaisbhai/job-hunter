interface Props {
  hasRuns: boolean;
}

export function EmptyState({ hasRuns }: Props) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-white/10 py-20 text-center">
      <p className="text-lg font-medium text-slate-300">
        {hasRuns ? "No matches in this run" : "No runs yet"}
      </p>
      <p className="max-w-sm text-sm text-slate-500">
        {hasRuns
          ? "Nothing scored at or above the match threshold this time."
          : "Click Run Now to scrape your configured job sites and see results here."}
      </p>
    </div>
  );
}
