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
  ClipboardList,
  FileQuestionMark,
  LoaderCircle,
  Pencil,
} from "lucide-react";
import { useState, useEffect } from "react";
import { z } from "zod";
import type { UserI } from "@/lib/types";
import { decodeId } from "@/lib/id-encoder";
import { useKeycloak } from "@/hooks/use-keycloak";

const detalheUCSearchSchema = z.object({
  ucId: z.string(),
});

export const Route = createFileRoute("/_layout/detalhes-uc")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function RouteComponent() {
  const { ucId } = Route.useSearch();
  const realId = decodeId(ucId);
  const { keycloak } = useKeycloak();
  const isManager =
    (keycloak.tokenParsed?.realm_access?.roles || []).find(
      (e) => e == "manager",
    ) != undefined;

  const { data: ucData } = useGetUcById(realId);
  const { data: students = [], isLoading: loadingStudents } =
    useGetUcStudents(realId);
  const { data: professors = [], isLoading: loadingProfs } =
    useGetUcProfessors(realId);
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(realId);

  const { data: allProfessors = [] } = useGetProfessors();
  const { data: allStudents = [] } = useGetStudents();

  const { mutate: deleteUc } = useDeleteUcById(realId);
  const { mutate: updateUc } = useUpdateUc(realId);

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
      <div className="flex flex-row gap-5 items-center justify-center text-5xl mb-35">
        <span className="font-rubik">{ucData?.name || "Carregando..."}</span>
        <Pencil
          className={`cursor-pointer size-12.5 ${isEditing ? "fill-black stroke-1 stroke-white" : ""}`}
          onClick={() => {
            setIsEditing(!isEditing);
          }}
        />
      </div>

      <div className="flex flex-col gap-15 items-center">
        <div className="flex flex-col gap-15 w-262.5">
          {loadingStudents || loadingProfs || loadingRegent ? (
            <div className="flex justify-center items-center w-full h-40">
              <LoaderCircle className="animate-spin size-16" />
            </div>
          ) : (
            <div className="flex flex-row gap-15 w-full">
              <div className="w-full flex flex-1 flex-col gap-7.5">
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
                  className="h-auto w-auto font-medium text-2xl py-2.5 cursor-pointer"
                  size="lg"
                  variant="destructive"
                  onClick={() => deleteUc(realId)}
                >
                  Apagar Unidade Curricular
                </Button>
                <Button
                  size="lg"
                  className="h-auto w-auto font-medium text-2xl py-2.5 cursor-pointer"
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
                {!isManager && (
                  <>
                    <Link to="/banco-questoes" search={{ ucId: ucId }}>
                      <Button className="cursor-pointer flex flex-row gap-5 h-auto w-auto px-4 py-4.5 bg-[#3263A8] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                        <span className="w-fit font-medium text-[26px]">
                          Banco de Perguntas
                        </span>
                        <FileQuestionMark className="size-12.5" />
                      </Button>
                    </Link>
                    <Link
                      to="/exames-uc"
                      search={{ ucId: ucId, ucName: ucData?.name || "" }}
                    >
                      <Button className="cursor-pointer flex flex-row gap-5 h-auto w-auto px-4 py-4.5 bg-[#2E2B50] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                        <span className="w-fit font-medium text-[26px]">
                          Exames
                        </span>
                        <ClipboardList className="size-12.5" />
                      </Button>
                    </Link>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
