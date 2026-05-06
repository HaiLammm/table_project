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
  jlpt_level: string | null;
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
