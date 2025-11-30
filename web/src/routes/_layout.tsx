import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout")({
  component: () => (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex flex-row w-full">
        <SidebarTrigger />
        <Outlet />
      </main>
    </SidebarProvider>
  ),
});
