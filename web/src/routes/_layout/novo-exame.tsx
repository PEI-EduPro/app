import { AppBreadcrumb } from "@/components/app-breadcrumb";
import {
  NovoExameForm,
  type NovoExameFormT,
} from "@/components/novo-exame-form";
import { createFileRoute } from "@tanstack/react-router";
import z from "zod";

const NovoExameUCSearchSchema = z.object({
  ucId: z.number(),
  ucName: z.string(),
  examId: z.number().optional(),
});

export const Route = createFileRoute("/_layout/novo-exame")({
  validateSearch: NovoExameUCSearchSchema,
  component: NovoExame,
});

function NovoExame() {
  const { ucId, ucName, examId } = Route.useSearch();

  // if examID exists, fetch exam data to edit
  // const { data: examData } = useGetExamById(examId)

  const examConfgExample: NovoExameFormT = {
    topics: [
      { id: "1", nome: "Topic 1" },
      { id: "2", nome: "Topic 2" },
      { id: "3", nome: "Topic 3" },
    ],
    number_questions: {
      "1": 5,
      "2": 3,
      "3": 2,
    },
    relative_quotations: {
      "1": 50,
      "2": 30,
      "3": 20,
    },
    number_exams: 1,
    fraction: 0,
  };

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
      <div className="flex justify-center text-5xl mb-35">
        {examId ? "Editar Exame" : "Novo Exame"}
      </div>
      <div className="flex flex-col items-center">
        <div className="w-[700px] h-auto">
          <NovoExameForm examData={examId ? examConfgExample : undefined} />
        </div>
      </div>
    </div>
  );
}
