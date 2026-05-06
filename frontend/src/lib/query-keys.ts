export const userKeys = {
  all: ["user"] as const,
  me: () => [...userKeys.all, "me"] as const,
  preferences: () => [...userKeys.all, "preferences"] as const,
  dataExport: () => [...userKeys.all, "data-export"] as const,
  dataExportStatus: (id: number) => [...userKeys.dataExport(), id, "status"] as const,
};
