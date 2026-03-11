import { RouterProvider, createRouter } from "@tanstack/react-router";

// Import the generated route tree
import { routeTree } from "./routeTree.gen";
import { useKeycloak } from "./hooks/use-keycloak";
import type { KeycloakContextValue } from "./lib/keycloak-provider";

// Create a new router instance
const router = createRouter({
  routeTree,
  context: { auth: undefined! as KeycloakContextValue },
});

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Render the app
export function App() {
  const { keycloak, initialized } = useKeycloak();

  if (!initialized) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <p className="text-muted-foreground animate-pulse">A carregar...</p>
      </div>
    );
  }

  return (
    <RouterProvider
      router={router}
      context={{
        auth: {
          keycloak,
          initialized,
        },
      }}
    />
  );
}
