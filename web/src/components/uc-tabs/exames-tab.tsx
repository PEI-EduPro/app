import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Plus, Search } from "lucide-react";
import { useGetExamConfig } from "@/hooks/use-exams";
import { useGetUCTopics } from "@/hooks/use-questions";
import { useMemo, useState } from "react";
import ExamCard from "../exam-card";
import { Button } from "../ui/button";
import { encodeId } from "@/lib/id-encoder";
import { NoQuestionsAlertDialog } from "../no-questions-alert-dialog";
import { NovoExameForm } from "../novo-exame-steps/novo-exame-form";
import type { GenerationStatus } from "@/lib/types";

type StatusFilter = "all" | GenerationStatus;

export default function ExamesTab({ realId }: { realId: number }) {
  const { data: examConfigs } = useGetExamConfig(realId);
  const { data: topics } = useGetUCTopics(realId);

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
  const [noQuestionsAlertOpen, setNoQuestionsAlertOpen] = useState(false);
  const [showExamModal, setShowExamModal] = useState(false);

  const filtered = useMemo(() => {
    if (!examConfigs) return [];
    return examConfigs.filter((el, index) => {
      const matchesStatus = statusFilter === "all" || el.status === statusFilter;
      const matchesSearch = !search || `Exame ${index + 1}`.toLowerCase().includes(search.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [examConfigs, statusFilter, search]);

  const indexMap = useMemo(() => {
    if (!examConfigs) return new Map<number, number>();
    return new Map(examConfigs.map((el, i) => [el.id, i]));
  }, [examConfigs]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 sticky top-10 z-10 bg-background py-2 -mx-4 px-4 md:-mx-6 md:px-6">
        <Button
          size="sm"
          onClick={() => {
            const hasQuestions = topics?.some(([, count]) => count > 0);
            if (!hasQuestions) {
              setNoQuestionsAlertOpen(true);
            } else {
              setShowExamModal(true);
            }
          }}
          className="gap-1 cursor-pointer h-auto"
        >
          <Plus className="h-4 w-4" />
          Novo Exame
        </Button>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as StatusFilter)}>
          <SelectTrigger className="w-44 shrink-0">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem className="cursor-pointer" value="all">Todos</SelectItem>
            <SelectItem className="cursor-pointer" value="PENDING">Pendente</SelectItem>
            <SelectItem className="cursor-pointer" value="PROCESSING">A processar</SelectItem>
            <SelectItem className="cursor-pointer" value="COMPLETED">Concluído</SelectItem>
            <SelectItem className="cursor-pointer" value="FAILED">Falhado</SelectItem>
          </SelectContent>
        </Select>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Pesquisar por nome..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
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
        {filtered.length === 0 && examConfigs && (
          <p className="text-center text-muted-foreground py-8">
            Nenhum exame encontrado.
          </p>
        )}
        {showExamModal && (
          <NovoExameForm
            ucID={realId}
            onClose={() => setShowExamModal(false)}
          />
        )}
        <NoQuestionsAlertDialog
          open={noQuestionsAlertOpen}
          onOpenChange={() => setNoQuestionsAlertOpen(false)}
        />
      </div>
    </div>
  );
}
