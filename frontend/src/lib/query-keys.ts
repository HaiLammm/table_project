export const userKeys = {
  all: ["user"] as const,
  me: () => [...userKeys.all, "me"] as const,
  preferences: () => [...userKeys.all, "preferences"] as const,
};
