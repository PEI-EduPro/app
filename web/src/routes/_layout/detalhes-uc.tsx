import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Button } from "@/components/ui/button";
import {
  useDeleteUcById,
  useGetUcById,
  useGetUcStudents,
  useGetUcProfessors,
  useGetUcRegent,
  useUpdateUc,
} from "@/hooks/use-ucs";
import { useGetProfessors, useGetStudents } from "@/hooks/use-users";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  BookOpen,
  ClipboardList,
  FileQuestionMark,
  LoaderCircle,
  Pencil,
} from "lucide-react";
import { useState, useEffect } from "react";
import { z } from "zod";
import type { UserI } from "@/lib/types";

const detalheUCSearchSchema = z.object({
  ucId: z.number(),
});

export const Route = createFileRoute("/_layout/detalhes-uc")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
});

function RouteComponent() {
  const { ucId } = Route.useSearch();

  const { data: ucData } = useGetUcById(ucId);
  const { data: students = [], isLoading: loadingStudents } =
    useGetUcStudents(ucId);
  const { data: professors = [], isLoading: loadingProfs } =
    useGetUcProfessors(ucId);
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(ucId);

  const { data: allProfessors = [] } = useGetProfessors();
  const { data: allStudents = [] } = useGetStudents();

  const { mutate: deleteUc } = useDeleteUcById(ucId);
  const { mutate: updateUc } = useUpdateUc(ucId);

  const [isEditing, setIsEditing] = useState<boolean>(false);

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

  const professorsData = professors.map((p) => ({
    id: p.id,
    nome: formatUserName(p),
    email: p.email || "",
  }));

  const allStudentsData = allStudents.map((s) => ({
    id: s.id,
    nome: formatUserName(s),
    email: s.email || "",
  }));

  const allProfessorsData = allProfessors.map((p) => ({
    id: p.id,
    nome: formatUserName(p),
    email: p.email || "",
  }));

  const [profsSelection, setProfsSelection] = useState<
    { id: string; nome: string; email: string }[]
  >([]);
  const [alunosSelection, setAlunosSelection] = useState<
    { id: string; nome: string; email: string }[]
  >([]);
  const [regentSelection, setRegentSelection] = useState<
    { id: string; nome: string; email: string }[]
  >([]);

  useEffect(() => {
    setProfsSelection(professorsData);
    setAlunosSelection(studentsData);
    if (regent) {
      setRegentSelection([
        {
          id: regent.id,
          nome: formatUserName(regent),
          email: regent.email || "",
        },
      ]);
    }
  }, [students, professors, regent]);

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page={ucData?.name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />
      <div className="flex flex-row gap-[20px] items-center justify-center text-5xl mb-35">
        <span className="font-rubik">{ucData?.name || "Carregando..."}</span>
        <Pencil
          className={`cursor-pointer size-[50px] ${isEditing ? "fill-black stroke-1 stroke-white" : ""}`}
          onClick={() => {
            setIsEditing(!isEditing);
          }}
        />
      </div>

      <div className="flex flex-col gap-[60px] items-center">
        <div className="flex flex-col gap-[60px] w-[1050px]">
          {loadingStudents || loadingProfs || loadingRegent ? (
            <div className="flex justify-center items-center w-full h-40">
              <LoaderCircle className="animate-spin size-16" />
            </div>
          ) : (
            <div className="flex flex-row gap-[60px] w-full">
              <div className="w-full flex flex-1 flex-col gap-[30px]">
                <div>
                  <span className="text-[26px] font-medium">Regente</span>
                  <CustomTable
                    data={
                      isEditing
                        ? allProfessorsData
                        : regent
                          ? regentSelection
                          : []
                    }
                    isSelectable={isEditing}
                    rowSelection={regentSelection}
                    onChange={(e) => {
                      if (isEditing && e.length <= 1) {
                        setRegentSelection(
                          e as { id: string; nome: string; email: string }[],
                        );
                      }
                    }}
                  />
                </div>
                <div>
                  <span className="text-[26px] font-medium">Professores</span>
                  <CustomTable
                    data={isEditing ? allProfessorsData : professorsData}
                    isSelectable={isEditing}
                    rowSelection={profsSelection}
                    onChange={(e) => {
                      setProfsSelection(
                        e as { id: string; nome: string; email: string }[],
                      );
                    }}
                  />
                </div>
              </div>
              <div className="w-full flex-1 h-inherit">
                <span className="text-[26px] font-medium">Alunos</span>
                <CustomTable
                  data={isEditing ? allStudentsData : studentsData}
                  rowNumber={15}
                  isSelectable={isEditing}
                  rowSelection={alunosSelection}
                  onChange={(e) => {
                    setAlunosSelection(
                      e as { id: string; nome: string; email: string }[],
                    );
                  }}
                />
              </div>
            </div>
          )}
          <div className="flex justify-between">
            {isEditing ? (
              <>
                <Button
                  className="h-auto w-auto font-medium text-2xl py-[10px] cursor-pointer"
                  size="lg"
                  variant="destructive"
                  onClick={() => deleteUc(ucId)}
                >
                  Apagar Unidade Curricular
                </Button>
                <Button
                  size="lg"
                  className="h-auto w-auto font-medium text-2xl py-[10px] cursor-pointer"
                  onClick={() => {
                    updateUc({
                      regent_keycloak_id: regentSelection[0].id,
                      student_keycloak_ids: alunosSelection.map((a) => a.id),
                      professor_keycloak_ids: profsSelection.map((a) => a.id),
                    });
                    setIsEditing(false);
                  }}
                >
                  Guardar
                </Button>
              </>
            ) : (
              <>
                {/* Ligar este botão "Manuais" quando estiver funcional */}
                <Link to="/detalhes-uc" search={{ ucId: ucId }}>
                  <Button className="cursor-pointer flex flex-row gap-[20px] h-auto w-auto px-[16px] py-[18px] bg-[#41B5C0] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                    <span className="w-fit font-medium text-[26px]">
                      Manuais
                    </span>
                    <BookOpen className="size-[50px]" />
                  </Button>
                </Link>
                <Link to="/banco-questoes" search={{ ucId: ucId }}>
                  <Button className="cursor-pointer flex flex-row gap-[20px] h-auto w-auto px-[16px] py-[18px] bg-[#3263A8] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                    <span className="w-fit font-medium text-[26px]">
                      Banco de Perguntas
                    </span>
                    <FileQuestionMark className="size-[50px]" />
                  </Button>
                </Link>
                <Link
                  to="/exames-uc"
                  search={{ ucId: ucId, ucName: ucData?.name || "" }}
                >
                  <Button className="cursor-pointer flex flex-row gap-[20px] h-auto w-auto px-[16px] py-[18px] bg-[#2E2B50] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                    <span className="w-fit font-medium text-[26px]">
                      Exames
                    </span>
                    <ClipboardList className="size-[50px]" />
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
