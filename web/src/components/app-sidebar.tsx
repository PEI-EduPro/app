import {
  Settings2,
  GraduationCap,
  BookOpen,
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

export function AppSidebar() {
  const { data: ucs } = useGetUc();
  const { keycloak } = useKeycloak();

  const items = [
    {
      title: "Manuais",
      icon: BookOpen,
      subContent: [
        { title: "Manual 1", url: "#" },
        { title: "Manual 2", url: "#" },
        { title: "Manual 3", url: "#" },
      ],
    },
    {
      title: "Unidades Curriculares",
      icon: GraduationCap,
      subContent:
        ucs?.map((uc) => ({
          title: uc.name,
          url: `/detalhes-uc?ucId=${uc.id}`,
        })) || [],
    },
  ];

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="#">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <SquareUserRound className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">
                    {keycloak.tokenParsed?.name || "Utilizador"}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {keycloak.tokenParsed?.email || "email não disponível"}
                  </span>
                </div>
              </a>
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
                        <div className="cursor-default">
                          <el.icon />
                          <span>{el.title}</span>
                          <ChevronDown className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
                        </div>
                      </SidebarMenuButton>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <SidebarMenuSub>
                        {el.subContent?.map((sub) => (
                          <SidebarMenuSubItem key={sub.title}>
                            <SidebarMenuSubButton href={sub.url}>
                              <span>{sub.title}</span>
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
                    <span>Definições</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenuButton asChild>
          <div
            className="cursor-pointer"
            onClick={() => {
              keycloak.logout({ redirectUri: window.location.origin });
            }}
          >
            <LogOutIcon />
            <span>Sair</span>
          </div>
        </SidebarMenuButton>
      </SidebarFooter>
    </Sidebar>
  );
}
