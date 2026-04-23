import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Plus } from "lucide-react";
import { useGetExamConfig } from "@/hooks/use-exams";
import { useMemo, useState } from "react";
import ExamCard from "../exam-card";
import { Button } from "../ui/button";
import { encodeId } from "@/lib/id-encoder";
import { NoQuestionsAlertDialog } from "../no-questions-alert-dialog";
import { NovoExameForm } from "../novo-exame-form";

export default function ExamesTab({ realId }: { realId: number }) {
  const { data: examConfigs } = useGetExamConfig(realId);

  const [search, setSearch] = useState("");
  const [noQuestionsAlertOpen, setNoQuestionsAlertOpen] = useState(false);
  const [filterField, setFilterField] = useState<
    "all" | "name" | "num_variations" | "fraction" | "num_questions"
  >("all");
  const [showExamModal, setShowExamModal] = useState(false);

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
    <div className="flex flex-col gap-4 mt-4">
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={() => {
            setShowExamModal(true);
          }}
          className="gap-1 cursor-pointer h-auto"
        >
          <Plus className="h-4 w-4" />
          Novo Exame
        </Button>
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
            <SelectItem className="cursor-pointer" value="all">
              Todos os campos
            </SelectItem>
            <SelectItem className="cursor-pointer" value="name">
              Nome
            </SelectItem>
            <SelectItem className="cursor-pointer" value="num_variations">
              Variações
            </SelectItem>
            <SelectItem className="cursor-pointer" value="fraction">
              Desconto (%)
            </SelectItem>
            <SelectItem className="cursor-pointer" value="num_questions">
              Nº Questões
            </SelectItem>
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

      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pt-2">
        {filtered.map((el) => (
          <ExamCard
            id={el.id}
            name={`Exame ${(indexMap.get(el.id) ?? 0) + 1}`}
            ucId={encodeId(realId)}
            key={el.id}
            examConfig={el}
          />
        ))}
        {filtered.length === 0 && examConfigs && examConfigs.length > 0 && (
          <p className="text-center text-muted-foreground py-8">
            Nenhum exame encontrado.
          </p>
        )}
        {showExamModal && (
          <NovoExameForm
            ucID={realId}
            onClose={() => {
              setShowExamModal(false);
            }}
          />
        )}
        <NoQuestionsAlertDialog
          open={noQuestionsAlertOpen}
          onOpenChange={setNoQuestionsAlertOpen}
          ucId={realId}
        />
      </div>
    </div>
  );
}
