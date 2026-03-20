import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Scanner } from "@yudiel/react-qr-scanner";
import { useGetUcById, useGetUcStudents } from "@/hooks/use-ucs";
import type { UserI } from "@/lib/types";
import { createFileRoute } from "@tanstack/react-router";
import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import z from "zod";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { decodeId } from "@/lib/id-encoder";

const detalheUCSearchSchema = z.object({
  ucId: z.string(),
});

export const Route = createFileRoute("/_layout/mobile_scan_teste")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function RouteComponent() {
  const { ucId } = Route.useSearch();
  const realId = decodeId(ucId);
  const { data: ucData } = useGetUcById(realId);
  const { data: students = [], isLoading: loadingStudents } =
    useGetUcStudents(realId);
  const [alunosSelection, setAlunosSelection] = useState<{
    id: string;
    nome: string;
    nmec: string;
  }>();
  const isRegent = false;

  const [canAssociate, setCanAssociate] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);

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

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page={ucData?.name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />
      <div className="font-rubik flex justify-center text-lg md:text-5xl mb-7 md:mb-25">
        <span className="font-rubik">{ucData?.name || "Carregando..."}</span>
      </div>

      <div className="flex flex-col gap-15 items-center">
        {loadingStudents ? (
          <div className="flex justify-center items-center w-full h-40">
            <LoaderCircle className="animate-spin size-16" />
          </div>
        ) : (
          <div className="flex flex-col justify-center gap-10 md:w-full">
            {isRegent && (
              <div className="flex flex-row justify-between items-center">
                <span className="text-sm font-medium">0/200</span>
                {isOpen ? (
                  <Button
                    className="cursor-pointer h-auto w-auto px-4 py-2 bg-red-500 border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none"
                    onClick={() => setIsOpen(false)}
                  >
                    <span className="w-fit font-medium">Fechar Exame</span>
                  </Button>
                ) : (
                  <Button
                    className="cursor-pointer h-auto w-auto px-4 py-2 bg-green-500 border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none"
                    onClick={() => setIsOpen(true)}
                  >
                    <span className="w-fit font-medium">Abrir Exame</span>
                  </Button>
                )}
              </div>
            )}
            <div className="flex flex-row justify-center">
              <Scanner
                onScan={() => {
                  setCanAssociate(true);
                }}
                paused={canAssociate}
                formats={["qr_code"]}
                styles={{
                  container: {
                    width: "70%",
                    aspectRatio: "1 / 1",
                    border: "2px dashed rgba(239, 68, 68, 0.4)",
                    borderRadius: "0.5rem",
                  },
                }}
                components={{
                  finder: false,
                }}
              />
            </div>
            <div className="md:w-full flex flex-1 flex-col">
              <span className="text-[26px] font-medium">Alunos</span>
              <CustomTable
                data={studentsData}
                rowNumber={15}
                isSelectable
                rowSelection={alunosSelection ? [alunosSelection] : []}
                onChange={(e) => {
                  const newSelection = e.filter(
                    (el) => el.id != alunosSelection?.id,
                  );
                  if (newSelection.length > 0) {
                    setAlunosSelection({
                      id: newSelection[0].id,
                      nome: newSelection[0].nome,
                      nmec: newSelection[0].nmec,
                    });
                  } else {
                    setAlunosSelection(undefined);
                  }
                }}
              />
            </div>
            <Button
              className="cursor-pointer h-auto w-auto px-4 py-4.5 bg-[#2E2B50] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none"
              disabled={
                isOpen ? !canAssociate || alunosSelection === undefined : true
              }
              onClick={() => {
                setCanAssociate(false);
                toast.success("Exame associado com sucesso!", {
                  position: "top-right",
                });
                setAlunosSelection(undefined);
              }}
            >
              <span className="w-fit font-medium text-[26px]">
                Associar aluno
              </span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
