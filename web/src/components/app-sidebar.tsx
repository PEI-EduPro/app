import {
  Settings2,
  GraduationCap,
  SquareUserRound,
  ChevronDown,
  LogOutIcon,
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

export function AppSidebar() {
  const { data: ucs } = useGetUc();
  const { keycloak } = useKeycloak();
  const isMobile = useIsMobile();

  const items = [
    {
      title: "Unidades Curriculares",
      icon: GraduationCap,
      subContent:
        ucs?.map((uc) => ({
          title: uc.name,
          url: isMobile
            ? `/mobile_evaluate_tests`
            : `/detalhes-uc?ucId=${encodeId(uc.id)}`,
        })) || [],
    },
  ];

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <div className="h-auto">
                <div className="flex aspect-square size-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <SquareUserRound className="size-8" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="text-xl font-semibold">
                    {keycloak.tokenParsed?.name || "Utilizador"}
                  </span>
                  <span className="text-xl text-muted-foreground">
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
                        <div className="cursor-pointer">
                          <el.icon />
                          <span className="text-base">{el.title}</span>
                          <ChevronDown className=" transition-transform group-data-[state=open]/collapsible:rotate-180" />
                        </div>
                      </SidebarMenuButton>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <SidebarMenuSub>
                        {el.subContent?.map((sub) => (
                          <SidebarMenuSubItem key={sub.title}>
                            <SidebarMenuSubButton href={sub.url}>
                              <span className="text-[16px]">{sub.title}</span>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        ))}
                      </SidebarMenuSub>
                    </CollapsibleContent>
                  </SidebarMenuItem>
                </Collapsible>
              ))}
              <SidebarMenuItem key="Definições">
                <SidebarMenuButton asChild>
                  <a href="#">
                    <Settings2 />
                    <span className="text-base">Definições</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t-2 border-gray-500">
        <SidebarMenuButton asChild>
          <div
            className="cursor-pointer"
            onClick={() => {
              keycloak.logout({ redirectUri: window.location.origin });
            }}
          >
            <LogOutIcon className="" />
            <span className="text-base">Sair</span>
          </div>
        </SidebarMenuButton>
      </SidebarFooter>
    </Sidebar>
  );
}
