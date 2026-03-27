import { usePwaInstallContext } from "@/lib/pwa-install-context";

export function usePwaInstall() {
  const { installPrompt, setInstallPrompt } = usePwaInstallContext();

  const install = async () => {
    if (!installPrompt) return;
    await installPrompt.prompt();
    setInstallPrompt(null);
  };

  return { canInstall: !!installPrompt, install };
}
