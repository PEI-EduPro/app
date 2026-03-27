import { createContext, useContext } from "react";

export interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
}

export const PwaInstallContext = createContext<{
  installPrompt: BeforeInstallPromptEvent | null;
  setInstallPrompt: (e: BeforeInstallPromptEvent | null) => void;
}>({ installPrompt: null, setInstallPrompt: () => {} });

export const usePwaInstallContext = () => useContext(PwaInstallContext);
