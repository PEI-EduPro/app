import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarTrigger, useSidebar } from "@/components/ui/sidebar";
import { useIsMobile } from "@/hooks/use-mobile";
import { createFileRoute, Outlet, redirect, useRouterState } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout")({
  component: LayoutComponent,
  beforeLoad: async ({ context }) => {
    const { keycloak, initialized } = context.auth;

    if (!keycloak.authenticated && initialized) {
      throw redirect({ to: "/" });
    }
  },
});

function SidebarHoverWrapper({ children }: { children: React.ReactNode }) {
  const { open, setOpen } = useSidebar();
  const isMobile = useIsMobile();

  if (isMobile) return <>{children}</>;

  return (
    <div
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      {children}
    </div>
  );
}

function LayoutComponent() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isMobile = useIsMobile();

  return (
    <SidebarProvider>
      <SidebarHoverWrapper>
        <AppSidebar />
      </SidebarHoverWrapper>
      <main className="flex flex-row w-full">
        {isMobile && <SidebarTrigger />}
        <div key={pathname} className="w-full animate-fade-in-up overflow-clip">
          <Outlet />
        </div>
      </main>
    </SidebarProvider>
  );
}
