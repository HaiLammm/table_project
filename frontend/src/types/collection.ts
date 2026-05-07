export interface Collection {
  id: number;
  name: string;
  icon: string;
  term_count: number;
  mastery_percent: number;
  created_at: string | null;
  updated_at: string | null;
}

export type CollectionResponse = Collection;

export interface CollectionListResponse {
  items: Collection[];
}

export interface CollectionCreateRequest {
  name: string;
  icon: string;
}

export interface CollectionUpdateRequest {
  name?: string;
  icon?: string;
}

export interface AddTermRequest {
  term_id: number;
}

export interface AddTermsRequest {
  term_ids: number[];
}

export interface AddTermsResponse {
  added: number;
  skipped: number;
}

export type CollectionTermMasteryStatus = "new" | "learning" | "mastered";

export interface CollectionTerm {
  term_id: number;
  term: string;
  language: string;
  mastery_status: CollectionTermMasteryStatus;
  added_at: string | null;
  cefr_level: string | null;
  jlpt_level: string | null;
  part_of_speech: string | null;
}

export interface CollectionTermListResponse {
  items: CollectionTerm[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface CollectionCSVImportError {
  row: number;
  error: string;
}

export interface CollectionCSVImportResponse {
  added: number;
  skipped: number;
  errors: CollectionCSVImportError[];
}
