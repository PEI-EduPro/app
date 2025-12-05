import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { NovoExameForm } from "@/components/novo-exame-form";
import { createFileRoute } from "@tanstack/react-router";
import z from "zod";

const NovoExameUCSearchSchema = z.object({
  ucId: z.number(),
  ucName: z.string(),
});

export const Route = createFileRoute("/_layout/novo-exame")({
  validateSearch: NovoExameUCSearchSchema,
  component: NovoExame,
});

function NovoExame() {
  const { ucId, ucName } = Route.useSearch();

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page="Novo Exame"
        crumbs={[
          {
            name: "Unidades Curriculares",
            link: "/unidades-curriculares",
          },
          {
            name: ucName,
            link: `/detalhes-uc?ucId=${ucId}`,
          },
        ]}
      />
      <div className="flex justify-center text-5xl mb-35">Novo Exame</div>
      <div className="flex flex-col items-center">
        <div className="w-[700px] h-auto">
          <NovoExameForm />
        </div>
      </div>
    </div>
  );
}
