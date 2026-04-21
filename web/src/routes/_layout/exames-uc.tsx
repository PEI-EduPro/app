import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { useGetUcById } from "@/hooks/use-ucs";
import { decodeId } from "@/lib/id-encoder";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";

import { CustomSwitch } from "@/components/custom-switch";
import ExamesUcExams from "@/components/exames-uc-exams";
import ExamesUcSalas from "@/components/exames-uc-salas";

const examesUCSearchSchema = z.object({
  ucId: z.string(),
  ucName: z.string(),
});

export const Route = createFileRoute("/_layout/exames-uc")({
  validateSearch: examesUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function RouteComponent() {
  const { ucId, ucName } = Route.useSearch();
  const realId = decodeId(ucId);

  const { data: ucData } = useGetUcById(realId);
  const [checked, setChecked] = useState<boolean>(false);

  return (
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-6 w-full">
      <div className="shrink-0">
        <AppBreadcrumb
          page="Exames"
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
                leftLabel="Exames"
                rightLabel="Salas"
              />
            </div>
            <div className="flex flex-col gap-2.5 items-center">
              <span className="font-rubik typography-h1">{ucData?.name}</span>
              <span className="font-rubik typography-h2 text-primary">
                {checked ? "Salas" : "Exames"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden px-47.5 py-1">
        {checked ? (
          <ExamesUcSalas realId={realId} ucName={ucName} />
        ) : (
          <ExamesUcExams realId={realId} ucName={ucName} />
        )}
      </div>
    </div>
  );
}
