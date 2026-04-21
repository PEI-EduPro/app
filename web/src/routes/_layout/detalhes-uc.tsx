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
import { useGetUCTopics } from "@/hooks/use-questions";
import { useGetExamConfig } from "@/hooks/use-exams";
import { createFileRoute, Link } from "@tanstack/react-router";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  ClipboardList,
  FileQuestionMark,
  LoaderCircle,
  Pencil,
  Trash2Icon,
} from "lucide-react";

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
  const { data: topics = [] } = useGetUCTopics(realId);
  const { data: exams = [] } = useGetExamConfig(realId);

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
        <div className="flex flex-row mb-25 items-center gap-4">
          <div className="flex flex-row gap-2 items-center shrink-0">
            {isEditing ? (
              <>
                <Button
                  size="sm"
                  variant="secondary"
                  className="cursor-pointer hover:bg-destructive hover:text-white"
                  onClick={() => setIsEditing(false)}
                >
                  Cancelar
                </Button>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      size="sm"
                      variant="destructive"
                      className="cursor-pointer"
                    >
                      Guardar
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                        <Pencil />
                      </AlertDialogMedia>
                      <AlertDialogTitle>
                        Guardar alterações
                      </AlertDialogTitle>
                      <AlertDialogDescription>
                        Esta ação irá guardar as alterações feitas à unidade
                        curricular. Deseja continuar?
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                      <AlertDialogCancel
                        variant="secondary"
                        size="lg"
                        className="cursor-pointer"
                      >
                        Cancelar
                      </AlertDialogCancel>
                      <AlertDialogAction
                        size="lg"
                        variant="destructive"
                        className="cursor-pointer"
                        onClick={() => {
                          if (regentSelection) {
                            updateUc({
                              regent_keycloak_id: regentSelection.id,
                              professor_keycloak_ids: profsSelection.map(
                                (a) => a.id,
                              ),
                            });
                            setIsEditing(false);
                          }
                        }}
                      >
                        Guardar
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </>
            ) : (
              <>
                <Link
                  to="/banco-questoes"
                  search={{ ucId: ucId }}
                  className="flex"
                >
                  <Button
                    size="sm"
                    className="gap-1 cursor-pointer bg-[#3263A8] hover:bg-[#3263A8]/90"
                  >
                    <FileQuestionMark className="h-4 w-4" />
                    Banco de Perguntas
                  </Button>
                </Link>
                <Link
                  to="/exames-uc"
                  search={{ ucId: ucId, ucName: ucData?.name || "" }}
                  className="flex"
                >
                  <Button
                    size="sm"
                    className="gap-1 cursor-pointer bg-[#2E2B50] hover:bg-[#2E2B50]/90"
                  >
                    <ClipboardList className="h-4 w-4" />
                    Exames
                  </Button>
                </Link>
                <Button
                  size="sm"
                  className="gap-1 cursor-pointer"
                  onClick={() => setIsEditing(true)}
                >
                  <Pencil className="h-4 w-4" />
                  Editar
                </Button>
              </>
            )}
          </div>
          <span className="font-rubik typography-h1 flex-1 text-center min-w-0 break-words">
            {ucData?.name || "Carregando..."}
          </span>
        </div>

        <div className="flex flex-col gap-15">
          {loadingProfs || loadingRegent ? (
            <div className="flex justify-center items-center w-full h-40">
              <LoaderCircle className="animate-spin size-16" />
            </div>
          ) : (
            <div className="flex flex-row gap-15">
              <div className="w-full flex flex-1 flex-col gap-7.5">
                <div>
                  <span className="typography-h4">Regente</span>
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
                  <span className="typography-h4">Professores</span>
                  <CustomTable
                    data={
                      isEditing
                        ? allProfessorsData.filter(
                            (el) => el.id !== regentSelection?.id,
                          )
                        : professorsData
                    }
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

          {isEditing && isManager && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  size="sm"
                  variant="destructive"
                  className="cursor-pointer w-fit"
                >
                  Apagar Unidade Curricular
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                    <Trash2Icon />
                  </AlertDialogMedia>
                  <AlertDialogTitle>
                    Apagar Unidade Curricular
                  </AlertDialogTitle>
                  <AlertDialogDescription>
                    {`Esta ação irá apagar permanentemente a unidade curricular ${ucData?.name}. Deseja continuar?`}
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                  <AlertDialogCancel
                    variant="outline"
                    className="cursor-pointer"
                    size="lg"
                  >
                    Cancelar
                  </AlertDialogCancel>
                  <AlertDialogAction
                    size="lg"
                    variant="destructive"
                    className="cursor-pointer"
                    onClick={() => deleteUc(realId)}
                  >
                    Apagar
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}

          {!isEditing && (
            <div className="flex flex-col gap-8">
              <div className="flex flex-col gap-3">
                <span className="typography-h4">Tópicos</span>
                {topics.length === 0 ? (
                  <span className="text-muted-foreground text-sm">
                    Nenhum tópico.
                  </span>
                ) : (
                  <ul className="flex flex-col gap-1">
                    {topics.map(([topic]) => (
                      <li
                        key={topic.id}
                        className="text-base px-3 py-2 rounded-md bg-muted/50"
                      >
                        {topic.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="flex flex-col gap-3">
                <span className="typography-h4">Exames</span>
                {exams.length === 0 ? (
                  <span className="text-muted-foreground text-sm">
                    Nenhum exame.
                  </span>
                ) : (
                  <ul className="flex flex-col gap-1">
                    {exams.map((exam, index) => {
                      const totalQuestions =
                        exam.topic_configs?.reduce(
                          (s, t) => s + (t.num_questions || 0),
                          0,
                        ) ?? 0;
                      return (
                        <li
                          key={exam.id}
                          className="flex items-center justify-between text-base px-3 py-2 rounded-md bg-muted/50"
                        >
                          <span>Exame {index + 1}</span>
                          <span className="text-sm text-muted-foreground flex gap-4">
                            <span>{exam.num_variations} versões</span>
                            <span>{totalQuestions} questões</span>
                            <span>{exam.fraction}% desconto</span>
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
