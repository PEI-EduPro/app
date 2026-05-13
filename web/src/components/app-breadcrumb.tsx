import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";
import { useKeycloak } from "@/hooks/use-keycloak.ts";
import { LogOut } from "lucide-react";

export interface BreadcrumbProps {
  page: string;
  crumbs?: {
    name: string;
    link: string;
  }[];
}

export function AppBreadcrumb(props: BreadcrumbProps) {
  const { crumbs, page } = props;
  const { keycloak } = useKeycloak();

  return (
    <div className="w-full mb-3.75 md:mb-7.5">
      <div className="flex flex-row justify-between align-center mb-1.5">
        <Breadcrumb className="w-full">
          <BreadcrumbList>
            {crumbs &&
              crumbs.map((el, index) => (
                <div key={index} className="flex items-center gap-1.5">
                  <BreadcrumbItem>
                    <BreadcrumbLink asChild>
                      <Link to={el.link} className="md:text-2xl">
                        {el.name}
                      </Link>
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="md:[&>svg]:size-6" />
                </div>
              ))}
            <BreadcrumbItem>
              <BreadcrumbPage className="md:text-2xl">{page}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <Button
          variant="destructive"
          onClick={() => keycloak.logout()}
          className="cursor-pointer flex items-center gap-2 h-auto py-1 md:py-1.5"
        >
          <span className="text-sm md:text-base">Sair</span>
          <LogOut className="size-4 md:size-5" />
        </Button>
      </div>
      <Separator
        style={{
          width: "100vw",
          position: "relative",
          left: "50%",
          transform: "translateX(-50%)",
        }}
      />
    </div>
  );
}
