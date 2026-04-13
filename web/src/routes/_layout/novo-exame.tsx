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
    <div className="flex flex-col h-full py-3.5 px-6 w-full overflow-hidden">
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
      <div className="flex justify-center text-5xl mb-4">
        {examId ? "Editar Exame" : "Novo Exame"}
      </div>
      <div className="flex flex-col items-center flex-1 min-h-0">
        <div className="w-175 flex flex-col flex-1 min-h-0">
          <NovoExameForm ucID={realId} ucName={ucName} />
        </div>
      </div>
    </div>
  );
}
