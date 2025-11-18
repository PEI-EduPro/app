import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { NovaUCForm } from "@/components/nova-uc-form";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout/nova-uc")({
  component: NovaUC,
});

function NovaUC() {
  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page="Nova Unidade Curricular"
        crumbs={[
          {
            name: "Unidades Curriculares",
            link: "/unidades-curriculares",
          },
        ]}
      />
      <div className="flex justify-center text-5xl mb-35">
        Nova Unidade Curricular
      </div>
      <div className="flex flex-col items-center">
        <div className="w-[450px] h-auto">
          <NovaUCForm />
        </div>
      </div>
    </div>
  );
}
