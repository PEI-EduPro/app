import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

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
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex flex-row w-full">
        <SidebarTrigger />
        <Outlet />
      </main>
    </SidebarProvider>
  );
}
