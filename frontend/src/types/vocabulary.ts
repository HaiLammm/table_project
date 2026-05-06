export interface VocabularyDefinition {
  id: number;
  language: string;
  definition: string;
  ipa: string | null;
  examples: string[];
  source: string;
  validated_against_jmdict: boolean;
}

export interface VocabularyTerm {
  id: number;
  term: string;
  language: string;
  parent_id: number | null;
  cefr_level: string | null;
  jlpt_level: number | null;
  part_of_speech: string | null;
  definitions: VocabularyDefinition[];
  created_at: string | null;
}

export interface PaginatedTermsResponse {
  items: VocabularyTerm[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface VocabularyFilterParams {
  page?: number;
  page_size?: number;
  cefr_level?: string | null;
  jlpt_level?: string | null;
  parent_id?: number | null;
}

export interface VocabularySearchParams {
  query: string;
  language?: string | null;
  limit?: number;
}

export interface VocabularyRequestCreate {
  topic: string;
  language: string;
  level: string;
  count: number;
}

export interface EnrichedTermPreview {
  term_id: number | null;
  candidate_id: string | null;
  term: string;
  language: string;
  definition: string | null;
  ipa: string | null;
  cefr_level: string | null;
  jlpt_level: number | null;
  examples: string[];
  source: "corpus" | "llm";
  validated_against_jmdict: boolean;
}

export interface VocabularyRequestPreviewResponse {
  preview_id: string | null;
  terms: EnrichedTermPreview[];
  corpus_match_count: number;
  gap_count: number;
  requested_count: number;
}

export interface VocabularyRequestConfirmRequest {
  preview_id: string;
  selected_candidate_ids: string[];
}

export interface VocabularyRequestConfirmResponse {
  added_count: number;
  skipped_count: number;
}

export interface CSVRowPreview {
  row_number: number;
  term: string | null;
  language: string | null;
  definition: string | null;
  tags: string | null;
  status: "valid" | "warning" | "error";
  error_message: string | null;
}

export interface CSVImportPreviewResponse {
  total_rows: number;
  valid_count: number;
  warning_count: number;
  error_count: number;
  preview_rows: CSVRowPreview[];
  detected_columns: string[];
}

export interface CSVImportResultResponse {
  imported_count: number;
  review_count: number;
  duplicates_skipped: number;
  errors: Array<{ row: number; error: string }>;
}