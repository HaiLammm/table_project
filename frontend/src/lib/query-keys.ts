export const userKeys = {
  all: ["user"] as const,
  me: () => [...userKeys.all, "me"] as const,
  preferences: () => [...userKeys.all, "preferences"] as const,
  dataExport: () => [...userKeys.all, "data-export"] as const,
  dataExportStatus: (id: number) => [...userKeys.dataExport(), id, "status"] as const,
};

export const srsKeys = {
  all: ["srs"] as const,
  queueStats: (collectionId?: number) =>
    [...srsKeys.all, "queue-stats", collectionId ?? null] as const,
  queue: (mode: "full" | "catchup", collectionId?: number) =>
    [...srsKeys.all, "queue", mode, collectionId ?? null] as const,
  card: (id: number) => [...srsKeys.all, "card", id] as const,
  dueCards: () => [...srsKeys.all, "due-cards"] as const,
  sessionStats: (sessionId: string) => [...srsKeys.all, "session-stats", sessionId] as const,
  schedule: () => [...srsKeys.all, "schedule"] as const,
};

export const diagnosticsKeys = {
  all: ["diagnostics"] as const,
  pendingInsights: (sessionId: string) =>
    [...diagnosticsKeys.all, "pending-insights", sessionId] as const,
};

export const collectionKeys = {
  all: ["collections"] as const,
  list: () => [...collectionKeys.all, "list"] as const,
  detail: (id: number) => [...collectionKeys.all, id] as const,
  terms: (id: number) => [...collectionKeys.detail(id), "terms"] as const,
};

export const vocabularyKeys = {
  all: ["vocabulary"] as const,
  list: (filters: Record<string, unknown>) => [...vocabularyKeys.all, "list", filters] as const,
  search: (query: string) => [...vocabularyKeys.all, "search", query] as const,
  detail: (id: number) => [...vocabularyKeys.all, "detail", id] as const,
  children: (parentId: number) => [...vocabularyKeys.all, "children", parentId] as const,
};

export const vocabularyRequestKeys = {
  all: ["vocabularyRequest"] as const,
  preview: () => [...vocabularyRequestKeys.all, "preview"] as const,
};

export const vocabularyImportKeys = {
  all: ["vocabularyImport"] as const,
  preview: () => [...vocabularyImportKeys.all, "preview"] as const,
  import: () => [...vocabularyImportKeys.all, "import"] as const,
};
