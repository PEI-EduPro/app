import {
  createFileRoute,
  Outlet,
  redirect,
  useRouterState,
} from "@tanstack/react-router";

export const Route = createFileRoute("/_layout")({
  component: LayoutComponent,
  beforeLoad: async ({ context }) => {
    const { keycloak, initialized } = context.auth;

    if (!keycloak.authenticated && initialized) {
      throw redirect({ to: "/" });
    }
  },
});

function LayoutComponent() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <main className="flex flex-row w-full h-screen overflow-hidden">
      <div
        key={pathname}
        className="w-full h-full animate-fade-in-up overflow-hidden"
      >
        <Outlet />
      </div>
    </main>
  );
}
