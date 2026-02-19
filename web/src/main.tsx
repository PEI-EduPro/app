import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { keycloak, keycloakInitOptions } from "./lib/keycloak.ts";
import { KeycloakProvider } from "./lib/keycloak-provider.tsx";

// Import the generated route tree
import { routeTree } from "./routeTree.gen";
import { Providers } from "./lib/providers";

// Create a new router instance
const router = createRouter({ routeTree });

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Render the app
const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
      <KeycloakProvider authClient={keycloak} initOptions={keycloakInitOptions}>
        <Providers>
          <RouterProvider router={router} />
        </Providers>
      </KeycloakProvider>
    </StrictMode>,
  );
}
