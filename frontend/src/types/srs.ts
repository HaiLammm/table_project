export type QueueMode = "full" | "catchup";

export interface EmbeddedTerm {
  id: number;
  term: string;
  language: string;
  cefr_level: string | null;
  jlpt_level: string | null;
  part_of_speech: string | null;
  definitions: Array<{
    id: number;
    language: string;
    definition: string;
    ipa: string | null;
    examples: string[];
    source: string;
    validated_against_jmdict: boolean;
  }>;
}

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
  term?: EmbeddedTerm | null;
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

export type RatingValue = 1 | 2 | 3 | 4;

export interface ReviewRequest {
  rating: RatingValue;
  response_time_ms: number | null;
  session_id?: string | null;
}

export interface ReviewResponse {
  id: number;
  due_at: string;
  fsrs_state: Record<string, unknown>;
  next_due_at: string;
  interval_display: string;
}

export interface SessionCard extends SrsCard {
  term: EmbeddedTerm | null;
}

export interface SessionStatsResponse {
  cards_reviewed: number
  cards_graduated: number
  cards_lapsed: number
  lapsed_card_ids: number[]
  tomorrow_due_count: number
  tomorrow_estimated_minutes: number
}

export interface ScheduleBucketResponse {
  due_count: number
  estimated_minutes: number
}

export interface UpcomingScheduleResponse {
  today: ScheduleBucketResponse
  tomorrow: ScheduleBucketResponse
  this_week: ScheduleBucketResponse
}

export interface CreateCardsForCollectionResponse {
  created_count: number
  skipped_count: number
}
