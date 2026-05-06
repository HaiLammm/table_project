import type { VocabularyTerm } from "@/types/vocabulary";

export type QueueMode = "full" | "catchup";

export interface SrsCard {
  id: number;
  term_id: number | null;
  language: string | null;
  due_at: string;
  fsrs_state: Record<string, unknown>;
  stability: number;
  difficulty: number;
  reps: number;
  lapses: number;
}

export interface DueCardsResponse {
  items: SrsCard[];
  total_count: number;
  limit: number;
  offset: number;
  mode: QueueMode;
}

export interface QueueStatsResponse {
  due_count: number;
  estimated_minutes: number;
  has_overdue: boolean;
  overdue_count: number;
  retention_rate?: number | null;
}

export interface ReviewRequest {
  rating: "again" | "hard" | "good" | "easy";
  elapsed_ms: number;
}

export interface ReviewResponse {
  id: number;
  due_at: string;
  fsrs_state: Record<string, unknown>;
}

export interface SessionCard extends SrsCard {
  term: VocabularyTerm | null;
}
