import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Link } from "@tanstack/react-router";

export interface BreadcrumbProps {
  page: string;
  crumbs?: [
    {
      name: string;
      link: string;
    },
  ];
}

export function AppBreadcrumb(props: BreadcrumbProps) {
  const { crumbs, page } = props;
  return (
    <Breadcrumb>
      <BreadcrumbList>
        {crumbs &&
          crumbs.map((el, index) => (
            <div key={index} className="flex items-center gap-1.5">
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to={el.link}>{el.name}</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
            </div>
          ))}
        <BreadcrumbItem>
          <BreadcrumbPage>{page}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}
