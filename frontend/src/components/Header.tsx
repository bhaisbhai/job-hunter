import type { Config } from "../types";

interface Props {
  config: Config | null;
  running: boolean;
  onRunNow: () => void;
}

export function Header({ config, running, onRunNow }: Props) {
  return (
    <header className="flex flex-col gap-4 border-b border-white/10 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="bg-gradient-to-r from-indigo-300 via-sky-200 to-emerald-200 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
          Job Hunter
        </h1>
        <p className="mt-1.5 max-w-xl text-sm text-slate-400">
          {config
            ? `${config.criteria.min_seniority} · ${config.criteria.industry} · ${config.criteria.location} — scoring ${config.target_urls.length} site(s) with ${config.llm_model}`
            : "Loading configuration…"}
        </p>
      </div>

      <button
        onClick={onRunNow}
        disabled={running}
        className="inline-flex items-center gap-2 self-start rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-950/50 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-indigo-500/40 sm:self-auto"
      >
        {running && (
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
        )}
        {running ? "Running…" : "Run Now"}
      </button>
    </header>
  );
}
