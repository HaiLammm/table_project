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
};
