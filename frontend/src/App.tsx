import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { EmptyState } from "./components/EmptyState";
import { Header } from "./components/Header";
import { ResultCard } from "./components/ResultCard";
import { RunSelector } from "./components/RunSelector";
import { StatsBar } from "./components/StatsBar";
import { StatusBanner } from "./components/StatusBanner";
import type { Config, Run, RunDetail } from "./types";

const ACTIVE_STATUSES = new Set(["pending", "scraping", "evaluating"]);

export default function App() {
  const [config, setConfig] = useState<Config | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadRunDetail = useCallback(async (runId: string) => {
    try {
      const detail = await api.getRun(runId);
      setRunDetail(detail);
      return detail;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return null;
    }
  }, []);

  useEffect(() => {
    api.getConfig().then(setConfig).catch((err) => setError(String(err)));
    api
      .listRuns()
      .then((fetchedRuns) => {
        setRuns(fetchedRuns);
        if (fetchedRuns.length > 0) {
          setSelectedRunId(fetchedRuns[0].id);
          loadRunDetail(fetchedRuns[0].id);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [loadRunDetail]);

  useEffect(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    if (!selectedRunId || !runDetail || !ACTIVE_STATUSES.has(runDetail.run.status)) {
      return;
    }

    pollRef.current = setInterval(async () => {
      const detail = await loadRunDetail(selectedRunId);
      if (detail && !ACTIVE_STATUSES.has(detail.run.status)) {
        const fetchedRuns = await api.listRuns();
        setRuns(fetchedRuns);
      }
    }, 2000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRunId, runDetail?.run.status, loadRunDetail]);

  const handleRunNow = useCallback(async () => {
    setError(null);
    try {
      const run = await api.triggerRun(true);
      setRuns((prev) => [run, ...prev]);
      setSelectedRunId(run.id);
      setRunDetail({ run, matches: [] });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  const handleSelectRun = useCallback(
    (runId: string) => {
      setSelectedRunId(runId);
      loadRunDetail(runId);
    },
    [loadRunDetail],
  );

  const running = runDetail ? ACTIVE_STATUSES.has(runDetail.run.status) : false;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-10">
        <Header config={config} running={running} onRunNow={handleRunNow} />

        {error && (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        {runs.length > 0 && (
          <div className="flex items-center justify-between gap-4">
            <RunSelector runs={runs} selectedRunId={selectedRunId} onSelect={handleSelectRun} />
          </div>
        )}

        {runDetail && (
          <>
            <StatusBanner run={runDetail.run} />
            {runDetail.run.listings_scraped > 0 && <StatsBar run={runDetail.run} />}

            {runDetail.matches.length > 0 && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {runDetail.matches.map((item) => (
                  <ResultCard key={item.id} item={item} />
                ))}
              </div>
            )}

            {!ACTIVE_STATUSES.has(runDetail.run.status) && runDetail.matches.length === 0 && (
              <EmptyState hasRuns />
            )}
          </>
        )}

        {!runDetail && runs.length === 0 && <EmptyState hasRuns={false} />}
      </div>
    </div>
  );
}
