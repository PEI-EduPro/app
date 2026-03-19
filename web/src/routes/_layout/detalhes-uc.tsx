import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Button } from "@/components/ui/button";
import {
  useDeleteUcById,
  useGetUcById,
  useGetUcProfessors,
  useGetUcRegent,
  useUpdateUc,
} from "@/hooks/use-ucs";
import { useGetProfessors } from "@/hooks/use-users";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ClipboardList, FileQuestionMark, LoaderCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { z } from "zod";
import type { UserI } from "@/lib/types";
import { decodeId } from "@/lib/id-encoder";
import { useKeycloak } from "@/hooks/use-keycloak";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

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

  const { data: professors = [], isLoading: loadingProfs } =
    useGetUcProfessors(realId);
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(realId);

  const { data: allProfessors = [] } = useGetProfessors();

  const { mutate: deleteUc } = useDeleteUcById(realId);
  const { mutate: updateUc } = useUpdateUc(realId);

  const [isEditing, setIsEditing] = useState<boolean>(false);

  const formatUserName = (user: UserI) =>
    user?.first_name && user?.last_name
      ? `${user.first_name} ${user.last_name}`
      : user?.firstName && user?.lastName
        ? `${user.firstName} ${user.lastName}`
        : user?.username || "";

  const professorsData = professors.map((p) => ({
    id: p.id,
    nome: formatUserName(p),
    email: p.email || "",
  }));

  const allProfessorsData = allProfessors.map((p) => ({
    id: p.id,
    nome: formatUserName(p),
    email: p.email || "",
  }));

  const [profsSelection, setProfsSelection] = useState<
    { id: string; nome: string; email: string }[]
  >([]);

  const [regentSelection, setRegentSelection] = useState<{
    id: string;
    nome: string;
    email: string;
  }>();

  useEffect(() => {
    setProfsSelection(professorsData);
    if (regent) {
      setRegentSelection({
        id: regent.id,
        nome: formatUserName(regent),
        email: regent.email || "",
      });
    }
  }, [professors, regent, isEditing]);

  return (
    <div className="py-3.5 px-6 w-full flex flex-col items-center">
      <AppBreadcrumb
        page={ucData?.name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />
      <div className="w-262.5">
        <div className="relative flex flex-row text-5xl mb-35 items-center">
          {isEditing && (
            <div className="absolute left-0">
              <Button
                size="lg"
                className="h-auto w-auto font-medium text-2xl py-2.5 cursor-pointer"
                variant="secondary"
                onClick={() => {
                  setIsEditing(false);
                }}
              >
                Cancelar
              </Button>
            </div>
          )}
          <span className="font-rubik w-full flex justify-center">
            {ucData?.name || "Carregando..."}
          </span>
          <div className="absolute right-0">
            <Button
              size="lg"
              className="h-auto w-auto font-medium text-2xl py-2.5 cursor-pointer"
              onClick={() => {
                if (!isEditing) {
                  setIsEditing(true);
                } else if (regentSelection) {
                  updateUc({
                    regent_keycloak_id: regentSelection.id,
                    professor_keycloak_ids: profsSelection.map((a) => a.id),
                  });
                  setIsEditing(false);
                }
              }}
            >
              {ucData && isEditing ? "Guardar" : "Editar"}
            </Button>
          </div>
        </div>

        <div className="flex flex-col gap-15 items-center">
          <div className="flex flex-col gap-15 w-full">
            {loadingProfs || loadingRegent ? (
              <div className="flex justify-center items-center w-full h-40">
                <LoaderCircle className="animate-spin size-16" />
              </div>
            ) : (
              <div className="flex flex-row gap-15">
                <div className="w-full flex flex-1 flex-col gap-7.5">
                  <div>
                    <span className="text-[26px] font-medium">Regente</span>

                    {isEditing && isManager ? (
                      <Select
                        value={
                          regentSelection?.id ?? "Nenhum resultado encontrado"
                        }
                        onValueChange={(e) => {
                          const option = allProfessors.find((el) => el.id == e);
                          if (option) {
                            setRegentSelection({
                              id: option.id,
                              email: option.email || "",
                              nome: `${option.firstName} ${option.lastName}`,
                            });
                          }
                        }}
                      >
                        <SelectTrigger className="shadow-none w-full">
                          <SelectValue placeholder="Selecione um docente" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectGroup>
                            {allProfessorsData.map((prof) => (
                              <SelectItem key={prof.id} value={prof.id}>
                                {prof.nome}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        readOnly
                        className="shadow-none"
                        value={
                          regentSelection?.nome ?? "Nenhum resultado encontrado"
                        }
                      />
                    )}
                  </div>
                </div>
                <div className="w-full flex-1 h-inherit">
                  <div>
                    <span className="text-[26px] font-medium">Professores</span>
                    <CustomTable
                      data={isEditing ? allProfessorsData : professorsData}
                      isSelectable={isEditing}
                      rowSelection={profsSelection}
                      rowNumber={10}
                      onChange={(e) => {
                        setProfsSelection(
                          e as { id: string; nome: string; email: string }[],
                        );
                      }}
                    />
                  </div>
                </div>
              </div>
            )}
            <div className="flex justify-between">
              {isEditing ? (
                <>
                  {isManager && (
                    <Button
                      className="h-auto w-auto font-medium text-2xl py-2.5 cursor-pointer"
                      size="lg"
                      variant="destructive"
                      onClick={() => deleteUc(realId)}
                    >
                      Apagar Unidade Curricular
                    </Button>
                  )}
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
    </div>
  );
}
