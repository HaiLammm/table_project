export type InsightSeverity = "info" | "warning" | "success";

export type PatternType =
  | "time_of_day_pattern"
  | "category_specific_weakness"
  | "cross_language_interference"
  | "response_time_anomaly"
  | "session_length_effect"
  | "day_of_week_pattern";

export interface DiagnosticInsight {
  id: number;
  type: PatternType;
  severity: InsightSeverity;
  icon: string;
  title: string;
  text: string;
  action_label?: string | null;
  action_href?: string | null;
  delivery_interval: number;
}

export interface PendingInsightsResponse {
  items: DiagnosticInsight[];
}

export interface InsightSeenRequest {
  session_id: string;
}

export interface InsightSeenResponse {
  success: boolean;
}
