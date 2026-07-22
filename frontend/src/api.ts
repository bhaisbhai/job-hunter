import type { Config, Run, RunDetail } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getConfig: () => request<Config>("/api/config"),
  listRuns: () => request<Run[]>("/api/runs"),
  getRun: (runId: string) => request<RunDetail>(`/api/runs/${runId}`),
  triggerRun: (sendEmail: boolean) =>
    request<Run>(`/api/runs?send_email=${sendEmail}`, { method: "POST" }),
};
