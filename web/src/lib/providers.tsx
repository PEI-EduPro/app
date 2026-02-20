import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools/production";
import { NuqsAdapter } from "nuqs/adapters/tanstack-router";
import { Toaster } from "@/components/ui/sonner";
import { keycloak, keycloakInitOptions } from "./keycloak";
import { KeycloakProvider } from "./keycloak-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient();
  return (
    <NuqsAdapter>
      <KeycloakProvider authClient={keycloak} initOptions={keycloakInitOptions}>
        <QueryClientProvider client={queryClient}>
          {children}
          {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
        </QueryClientProvider>
      </KeycloakProvider>
      <Toaster />
    </NuqsAdapter>
  );
}
