import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Card } from "@/components/ui/card";
import { useGetUcById, useGetUcStudents } from "@/hooks/use-ucs";
import type { UserI } from "@/lib/types";
import { createFileRoute } from "@tanstack/react-router";
import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import z from "zod";

const detalheUCSearchSchema = z.object({
  ucId: z.number(),
});

export const Route = createFileRoute("/_layout/mobile_scan_teste")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
});

function RouteComponent() {
  const { ucId } = Route.useSearch();

  const { data: ucData } = useGetUcById(ucId);
  const { data: students = [], isLoading: loadingStudents } =
    useGetUcStudents(ucId);
  const [alunosSelection, setAlunosSelection] = useState<
    { id: string; nome: string; nmec: string }[]
  >([]);

  const formatUserName = (user: UserI) =>
    user?.first_name && user?.last_name
      ? `${user.first_name} ${user.last_name}`
      : user?.firstName && user?.lastName
        ? `${user.firstName} ${user.lastName}`
        : user?.username || "";

  const studentsData = students.map((s) => ({
    id: s.id,
    nome: formatUserName(s),
    email: s.email || "",
  }));

  const studentsDataMock = [
    {
      id: "111111",
      nmec: "123456",
      nome: "bla bla bla",
    },
    {
      id: "111112",
      nmec: "123457",
      nome: "ble ble ble",
    },
    {
      id: "111113",
      nmec: "123458",
      nome: "bli bli bli",
    },
    {
      id: "111114",
      nmec: "123459",
      nome: "blo blo blo",
    },
    {
      id: "111115",
      nmec: "123460",
      nome: "blu blu blu",
    },
    {
      id: "111116",
      nmec: "123461",
      nome: "bls bls bls",
    },
  ];
  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page={ucData?.name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />
      <div className="font-rubik flex justify-center text-lg md:text-5xl mb-7 md:mb-35">
        <span className="font-rubik">{ucData?.name || "Carregando..."}</span>
      </div>

      <div className="flex flex-col gap-15 items-center">
        {loadingStudents ? (
          <div className="flex justify-center items-center w-full h-40">
            <LoaderCircle className="animate-spin size-16" />
          </div>
        ) : (
          <div className="flex flex-col justify-center gap-15 md:w-full">
            <div className="flex flex-row gap-15 w-full">
              <Card></Card>
            </div>
            <div className="md:w-full flex flex-1 flex-col gap-7.5">
              <span className="text-[26px] font-medium">Alunos</span>
              <CustomTable
                data={studentsDataMock}
                rowNumber={15}
                isSelectable
                rowSelection={alunosSelection}
                onChange={(e) => {
                  setAlunosSelection(
                    e as { id: string; nome: string; nmec: string }[],
                  );
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
