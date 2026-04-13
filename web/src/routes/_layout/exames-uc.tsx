import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { ExamConfigCard } from "@/components/exam-config-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDeleteExamConfig, useGetExamConfig } from "@/hooks/use-exams";
import { useGetUcById } from "@/hooks/use-ucs";
import { decodeId } from "@/lib/id-encoder";
import type { ExamConfigI } from "@/lib/types";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Search, Plus, Trash2Icon } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { z } from "zod";
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

const ContentActionCard = ({
  name,
  examConfig,
  ucId,
  id,
}: {
  id: number;
  name: string;
  ucId: string;
  examConfig: ExamConfigI;
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = useCallback(() => setIsModalOpen(true), []);
  const handleCloseModal = useCallback(() => setIsModalOpen(false), []);
  const deleteMutation = useDeleteExamConfig(decodeId(ucId));

  const totalQuestions =
    examConfig.topic_configs?.reduce(
      (sum, t) => sum + (t.num_questions || 0),
      0,
    ) ?? 0;

  return (
    <>
      <Card
        className="group flex flex-row items-center gap-4 px-5 py-4 cursor-pointer border border-[#3263A8]/20 bg-linear-to-r from-[#3263A8]/5 to-[#2E2B50]/5 hover:from-[#3263A8]/15 hover:to-[#2E2B50]/15 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 overflow-hidden"
        onClick={handleOpenModal}
      >
        <div className="shrink-0 w-1 self-stretch rounded-full bg-linear-to-b from-[#41B5C0] to-[#3263A8]" />

        <div className="flex-1 min-w-0">
          <span className="text-base font-semibold text-[#2E2B50] truncate block">
            {name}
          </span>
          <span className="text-xs text-muted-foreground">
            {examConfig.topic_configs?.length ?? 0} tópico
            {examConfig.topic_configs?.length !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="text-center">
            <p className="text-xs text-muted-foreground leading-none mb-0.5">
              Variações
            </p>
            <p className="text-lg font-bold text-[#3263A8] leading-none">
              {examConfig.num_variations}
            </p>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="text-center">
            <p className="text-xs text-muted-foreground leading-none mb-0.5">
              Desconto
            </p>
            <p className="text-lg font-bold text-[#3263A8] leading-none">
              {examConfig.fraction}%
            </p>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="text-center">
            <p className="text-xs text-muted-foreground leading-none mb-0.5">
              Questões
            </p>
            <p className="text-lg font-bold text-[#3263A8] leading-none">
              {totalQuestions}
            </p>
          </div>
        </div>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => e.stopPropagation()}
              className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:text-red-500 hover:bg-red-50 rounded-full"
            >
              <Trash2Icon className="h-4 w-4" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                <Trash2Icon />
              </AlertDialogMedia>
              <AlertDialogTitle className="font-medium text-2xl">
                Apagar Configuração de Exame
              </AlertDialogTitle>
              <AlertDialogDescription className="font-medium text-xl">
                Esta ação irá apagar permanentemente a configuração de exame.
                Deseja continuar?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter className="w-full! flex flex-row justify-between!">
              <AlertDialogCancel
                variant="outline"
                className="cursor-pointer text-xl"
                size="lg"
              >
                Cancelar
              </AlertDialogCancel>
              <AlertDialogAction
                size="lg"
                variant="destructive"
                className="cursor-pointer text-xl"
                onClick={() => deleteMutation.mutate(id)}
              >
                Apagar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Card>

      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={handleCloseModal}
        >
          <div
            className="bg-white rounded-xl shadow-2xl max-w-lg w-full m-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <ExamConfigCard examConfigData={examConfig} />
          </div>
        </div>
      )}
    </>
  );
};

function RouteComponent() {
  const { ucId, ucName } = Route.useSearch();
  const realId = decodeId(ucId);

  const { data: ucData } = useGetUcById(realId);
  const { data: examConfigs } = useGetExamConfig(realId);

  const [search, setSearch] = useState("");
  const [filterField, setFilterField] = useState<
    "all" | "name" | "num_variations" | "fraction" | "num_questions"
  >("all");

  const filtered = useMemo(() => {
    if (!examConfigs) return [];
    const q = search.toLowerCase();
    return examConfigs.filter((el, index) => {
      if (!q) return true;
      const name = `Exame ${index + 1}`;
      const totalQuestions =
        el.topic_configs?.reduce((s, t) => s + (t.num_questions || 0), 0) ?? 0;
      if (filterField === "all")
        return (
          name.toLowerCase().includes(q) ||
          String(el.num_variations).includes(q) ||
          String(el.fraction).includes(q) ||
          String(totalQuestions).includes(q)
        );
      if (filterField === "name") return name.toLowerCase().includes(q);
      if (filterField === "num_variations")
        return !isNaN(Number(q)) && el.num_variations >= Number(q);
      if (filterField === "fraction") return String(el.fraction).includes(q);
      return String(totalQuestions).includes(q);
    });
  }, [examConfigs, search, filterField]);

  const indexMap = useMemo(() => {
    if (!examConfigs) return new Map<number, number>();
    return new Map(examConfigs.map((el, i) => [el.id, i]));
  }, [examConfigs]);

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
        <div className="flex flex-col gap-2.5 items-center justify-center mb-8">
          <span className="font-rubik text-5xl">{ucData?.name}</span>
          <span className="font-rubik text-4xl text-primary">Exames</span>
        </div>

        <div className="px-47.5 mb-4 flex gap-2 mb-12">
          <Select
            value={filterField}
            onValueChange={(v) => {
              setFilterField(v as typeof filterField);
              setSearch("");
            }}
          >
            <SelectTrigger className="w-44 shrink-0">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os campos</SelectItem>
              <SelectItem value="name">Nome</SelectItem>
              <SelectItem value="num_variations">Variações</SelectItem>
              <SelectItem value="fraction">Desconto (%)</SelectItem>
              <SelectItem value="num_questions">Nº Questões</SelectItem>
            </SelectContent>
          </Select>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder={
                filterField === "all"
                  ? "Pesquisar exames..."
                  : filterField === "name"
                    ? "ex: Exame 1"
                    : filterField === "num_variations"
                      ? "mínimo de variações"
                      : filterField === "fraction"
                        ? "ex: 25"
                        : "ex: 10"
              }
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          {search && (
            <Button
              variant="ghost"
              onClick={() => setSearch("")}
              className="text-muted-foreground shrink-0"
            >
              Limpar
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-47.5 flex flex-col gap-3 pt-2">
        {filtered.map((el) => (
          <ContentActionCard
            id={el.id}
            name={`Exame ${(indexMap.get(el.id) ?? 0) + 1}`}
            ucId={ucId}
            key={el.id}
            examConfig={el}
          />
        ))}
        {filtered.length === 0 && examConfigs && examConfigs.length > 0 && (
          <p className="text-center text-muted-foreground py-8">
            Nenhum exame encontrado.
          </p>
        )}
        <Link to="/novo-exame" search={{ ucId: ucId, ucName: ucName }}>
          <Card className="flex-row justify-center items-center gap-2 px-5 py-4 border-2 border-dashed border-primary/40 bg-primary/5 hover:bg-primary/10 hover:border-primary/70 hover:-translate-y-1 cursor-pointer shadow-none group/add">
            <Plus className="text-primary h-8 w-8 transition-transform duration-300 group-hover/add:rotate-90" />
            <span className="text-base font-medium text-primary">
              Criar Exame
            </span>
          </Card>
        </Link>
      </div>
    </div>
  );
}
