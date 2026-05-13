import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { decodeId } from "@/lib/id-encoder";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";
import { CustomSwitch } from "@/components/custom-switch";
import StudentsQRCodes from "@/components/exames-correcao/students-qrcodes";
import ExamsCorrectionValidation from "@/components/exames-correcao/exams-correction-validation";

const examesUCSearchSchema = z.object({
  ucId: z.string(),
  ucName: z.string(),
  wrId: z.string(),
  wrName: z.string(),
});

export const Route = createFileRoute("/_layout/exames-correcao")({
  validateSearch: examesUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
    wrId: decodeId(search.wrId),
  }),
});

function RouteComponent() {
  const { ucId, ucName, wrId, wrName } = Route.useSearch();
  const realId = decodeId(wrId);

  const [checked, setChecked] = useState<boolean>(false);

  return (
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-4 md:px-6 w-full">
      <div className="shrink-0">
        <AppBreadcrumb
          page={wrName}
          crumbs={[
            { name: "Unidades Curriculares", link: "/unidades-curriculares" },
            { name: ucName, link: `/detalhes-uc?ucId=${ucId}` },
          ]}
        />

        <div className="w-full">
          <div className="relative flex items-center justify-center mb-8">
            <div className="absolute left-47.5">
              <CustomSwitch
                checked={checked}
                onCheckedChange={setChecked}
                leftLabel="Alunos"
                rightLabel="Testes"
              />
            </div>
            <div className="flex flex-col gap-2.5 items-center">
              <span className="font-rubik typography-h1">{wrName}</span>
              <span className="font-rubik typography-h2 text-primary">
                {checked ? "Testes" : "Alunos"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden px-47.5 py-1">
        {checked ? (
          <ExamsCorrectionValidation wrId={realId} />
        ) : (
          <StudentsQRCodes wrId={realId} />
        )}
      </div>
    </div>
  );
}
