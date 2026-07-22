import type { JobMatch } from "../types";
import { ScoreBadge } from "./ScoreBadge";

interface Props {
  job: JobMatch;
}

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function JobCard({ job }: Props) {
  return (
    <a
      href={job.url}
      target="_blank"
      rel="noreferrer"
      className="group flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition hover:-translate-y-0.5 hover:border-indigo-400/40 hover:bg-white/[0.06] hover:shadow-lg hover:shadow-indigo-950/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-base font-semibold text-slate-100 group-hover:text-white">
            {job.job_title}
          </h3>
          <p className="mt-0.5 truncate text-sm text-slate-400">{job.company}</p>
        </div>
        <ScoreBadge score={job.match_score} />
      </div>

      <p className="line-clamp-3 text-sm leading-relaxed text-slate-400">{job.reasoning}</p>

      <div className="mt-auto flex items-center justify-between gap-2 pt-1 text-xs text-slate-500">
        <span className="truncate rounded-full bg-white/5 px-2.5 py-1">
          {hostnameOf(job.source_url)}
        </span>
        {job.salary_range && (
          <span className="shrink-0 rounded-full bg-white/5 px-2.5 py-1 font-medium text-slate-300">
            {job.salary_range}
          </span>
        )}
      </div>
    </a>
  );
}
