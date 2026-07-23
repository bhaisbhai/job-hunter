export type RunStatus = "pending" | "scraping" | "evaluating" | "completed" | "failed";

export interface Run {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: RunStatus;
  listings_scraped: number;
  evaluated_count: number;
  evaluation_failures: number;
  matched_count: number;
  email_sent: boolean;
  error_message: string | null;
}

export interface ScoutedItem {
  id: number;
  run_id: string;
  title: string;
  subtitle: string;
  url: string;
  price: string | null;
  match_score: number;
  reasoning: string;
  source_url: string;
}

export interface RunDetail {
  run: Run;
  matches: ScoutedItem[];
}

export interface Config {
  scout: {
    name: string;
    instructions: string;
    min_match_score: number;
  };
  target_urls: string[];
  destination_email: string;
  llm_model: string;
}
