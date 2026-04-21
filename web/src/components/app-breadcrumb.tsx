import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { Link } from "@tanstack/react-router";

export interface BreadcrumbProps {
  page: string;
  crumbs?: {
    name: string;
    link: string;
  }[];
}

export function AppBreadcrumb(props: BreadcrumbProps) {
  const { crumbs, page } = props;
  return (
    <div className="w-full mb-3.75 md:mb-7.5">
      <Breadcrumb className="w-full mb-1.5">
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
