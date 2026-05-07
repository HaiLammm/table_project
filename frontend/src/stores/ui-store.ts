import { create } from "zustand";

type UIStore = {
  reviewInProgress: boolean;
  sidebarCollapsed: boolean;
  setReviewInProgress: (active: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;
};

export const useUIStore = create<UIStore>((set) => ({
  reviewInProgress: false,
  sidebarCollapsed: false,
  setReviewInProgress: (active) => set({ reviewInProgress: active }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleSidebarCollapsed: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}));
