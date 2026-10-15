import { create } from 'zustand';

/** Open state of the feedback dialog, shared by the floating button and the
 *  "Report a problem" entry in the More sheet. */
interface FeedbackDialogState {
  open: boolean;
  openDialog: () => void;
  closeDialog: () => void;
}

export const useFeedbackDialog = create<FeedbackDialogState>()((set) => ({
  open: false,
  openDialog: () => set({ open: true }),
  closeDialog: () => set({ open: false }),
}));
