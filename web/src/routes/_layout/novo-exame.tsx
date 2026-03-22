import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { NovoExameForm } from "@/components/novo-exame-form";
import { decodeId } from "@/lib/id-encoder";
import { createFileRoute } from "@tanstack/react-router";
import z from "zod";

const NovoExameUCSearchSchema = z.object({
  ucId: z.string(),
  ucName: z.string(),
  examId: z.number().optional(),
});

export const Route = createFileRoute("/_layout/novo-exame")({
  validateSearch: NovoExameUCSearchSchema,
  component: NovoExame,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function NovoExame() {
  const { ucId, ucName, examId } = Route.useSearch();
  const realId = decodeId(ucId);

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page={examId ? "Editar Exame" : "Novo Exame"}
        crumbs={[
          {
            name: "Unidades Curriculares",
            link: "/unidades-curriculares",
          },
          {
            name: ucName,
            link: `/detalhes-uc?ucId=${ucId}`,
          },
          {
            name: "Exames",
            link: `/exames-uc?ucId=${ucId}&ucName=${ucName}`,
          },
        ]}
      />
      <div className="flex justify-center text-5xl mb-25">
        {examId ? "Editar Exame" : "Novo Exame"}
      </div>
      <div className="flex flex-col items-center">
        <div className="w-175 h-auto">
          <NovoExameForm ucID={realId} ucName={ucName} />
        </div>
      </div>
    </div>
  );
}
