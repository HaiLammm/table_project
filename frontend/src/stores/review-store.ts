import { create } from "zustand";

type ReviewStore = {
  queueMode: "full" | "catchup";
  setQueueMode: (mode: "full" | "catchup") => void;
};

export const useReviewStore = create<ReviewStore>((set) => ({
  queueMode: "full",
  setQueueMode: (mode) => set({ queueMode: mode }),
}));
