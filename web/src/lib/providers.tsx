import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools/production";
import { NuqsAdapter } from "nuqs/adapters/tanstack-router";
import { Toaster } from "@/components/ui/sonner";
import { keycloak, keycloakInitOptions } from "./keycloak";
import { KeycloakProvider } from "./keycloak-provider";
import { useState, useEffect } from "react";
import { PwaInstallContext, type BeforeInstallPromptEvent } from "./pwa-install-context";

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient();
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  return (
    <PwaInstallContext.Provider value={{ installPrompt, setInstallPrompt }}>
      <NuqsAdapter>
        <KeycloakProvider authClient={keycloak} initOptions={keycloakInitOptions}>
          <QueryClientProvider client={queryClient}>
            {children}
            {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
          </QueryClientProvider>
        </KeycloakProvider>
        <Toaster />
      </NuqsAdapter>
    </PwaInstallContext.Provider>
  );
}
