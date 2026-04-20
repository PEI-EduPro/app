import {
  GraduationCap,
  SquareUserRound,
  ChevronDown,
  LogOutIcon,
  Download,
} from "lucide-react";
import {
  SidebarContent,
  Sidebar,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  SidebarHeader,
  SidebarFooter,
} from "./ui/sidebar";

import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "./ui/collapsible";
import { useGetUc } from "@/hooks/use-ucs";
import { useKeycloak } from "@/hooks/use-keycloak.ts";
import { useIsMobile } from "@/hooks/use-mobile";
import { encodeId } from "@/lib/id-encoder";
import { usePwaInstall } from "@/hooks/use-pwa-install";
import { useGetWaitingRooms } from "@/hooks/use-waiting-rooms";

export function AppSidebar() {
  const isMobile = useIsMobile();
  const { data: ucs } = useGetUc();
  const { data: waitingRooms } = useGetWaitingRooms({ enabled: isMobile });
  const { keycloak } = useKeycloak();
  const { canInstall, install } = usePwaInstall();

  const items = [
    {
      title: isMobile ? "Salas de Espera" : "Unidades Curriculares",
      icon: GraduationCap,
      subContent: isMobile
        ? waitingRooms?.map((wr) => ({
            title: `${wr.subject_name} — ${wr.exam_name}`,
            url:
              wr.state !== "closed"
                ? `/mobile_scan_teste?ucId=${encodeId(wr.waiting_room_id)}`
                : `/mobile_evaluate_tests?ucId=${encodeId(wr.waiting_room_id)}`,
            key: String(wr.waiting_room_id),
          })) || []
        : ucs?.map((uc) => ({
            title: uc.name,
            url: `/detalhes-uc?ucId=${encodeId(uc.id)}`,
            key: String(uc.id),
          })) || [],
    },
  ];

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border pb-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <div className="h-auto group-data-[collapsible=icon]:justify-center">
                <div className="flex aspect-square size-12 shrink-0 items-center justify-center rounded-xl bg-[#41B5C0] text-white shadow-md shadow-[#41B5C0]/40 group-data-[collapsible=icon]:size-8">
                  <SquareUserRound className="size-7 group-data-[collapsible=icon]:size-5" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none group-data-[collapsible=icon]:hidden">
                  <span className="text-base font-semibold text-sidebar-foreground">
                    {keycloak.tokenParsed?.name || "Utilizador"}
                  </span>
                  <span className="text-xs text-sidebar-foreground/60">
                    {keycloak.tokenParsed?.email || "email não disponível"}
                  </span>
                </div>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((el) => (
                <Collapsible key={el.title} className="group/collapsible">
                  <SidebarMenuItem key={el.title}>
                    <CollapsibleTrigger asChild>
                      <SidebarMenuButton asChild>
                        <div className="cursor-pointer rounded-lg hover:bg-[#41B5C0]/20 text-sidebar-foreground">
                          <el.icon className="text-[#41B5C0] size-5! shrink-0" />
                          <span className="text-base">{el.title}</span>
                          <ChevronDown className="ml-auto size-5! shrink-0 transition-transform duration-300 group-data-[state=open]/collapsible:rotate-180 text-[#41B5C0]" />
                        </div>
                      </SidebarMenuButton>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="overflow-hidden data-[state=closed]:animate-[collapsible-up_200ms_ease] data-[state=open]:animate-[collapsible-down_200ms_ease]">
                      <SidebarMenuSub>
                        {el.subContent?.map((sub, i) => (
                          <SidebarMenuSubItem
                            key={sub.key ?? `${sub.title}-${i}`}
                          >
                            <SidebarMenuSubButton
                              href={sub.url}
                              className="text-sidebar-foreground/80 hover:text-white hover:bg-[#3263A8]/40"
                            >
                              <span className="text-[15px]">{sub.title}</span>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        ))}
                      </SidebarMenuSub>
                    </CollapsibleContent>
                  </SidebarMenuItem>
                </Collapsible>
              ))}

              {canInstall && isMobile && (
                <SidebarMenuItem key="instalar">
                  <SidebarMenuButton
                    className="cursor-pointer text-sidebar-foreground hover:bg-[#41B5C0]/20"
                    onClick={install}
                  >
                    <Download className="w-4 h-4 text-[#41B5C0]" />
                    <span className="text-base">Instalar aplicação</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <SidebarMenuButton asChild>
          <div
            className="cursor-pointer text-sidebar-foreground/70 hover:text-red-400 hover:bg-red-500/10 rounded-lg"
            onClick={() => {
              keycloak.logout({ redirectUri: window.location.origin });
            }}
          >
            <LogOutIcon />
            <span className="text-base">Sair</span>
          </div>
        </SidebarMenuButton>
      </SidebarFooter>
    </Sidebar>
  );
}
