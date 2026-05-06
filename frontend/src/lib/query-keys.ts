export const userKeys = {
  all: ["user"] as const,
  me: () => [...userKeys.all, "me"] as const,
  preferences: () => [...userKeys.all, "preferences"] as const,
  dataExport: () => [...userKeys.all, "data-export"] as const,
  dataExportStatus: (id: number) => [...userKeys.dataExport(), id, "status"] as const,
};

export const srsKeys = {
  all: ["srs"] as const,
  queueStats: () => [...srsKeys.all, "queue-stats"] as const,
  queue: (mode: "full" | "catchup") => [...srsKeys.all, "queue", mode] as const,
  card: (id: number) => [...srsKeys.all, "card", id] as const,
  dueCards: () => [...srsKeys.all, "due-cards"] as const,
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
