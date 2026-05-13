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
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { DownloadIcon, Trash2Icon } from "lucide-react";
import { useCallback, useState } from "react";
import type { ExamConfigI, GenerationStatus } from "@/lib/types";
import { ExamConfigCard } from "@/components/exam-config-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const statusConfig: Record<GenerationStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  PENDING:    { label: "Pendente",    variant: "secondary" },
  PROCESSING: { label: "A processar", variant: "default" },
  COMPLETED:  { label: "Concluído",   variant: "outline" },
  FAILED:     { label: "Falhado",     variant: "destructive" },
};
import { useDeleteExamConfig, useDownloadExamConfig } from "@/hooks/use-exams";
import { decodeId } from "@/lib/id-encoder";

export default function ExamCard({
  name,
  examConfig,
  ucId,
  id,
}: {
  id: number;
  name: string;
  ucId: string;
  examConfig: ExamConfigI;
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = useCallback(() => setIsModalOpen(true), []);
  const handleCloseModal = useCallback(() => setIsModalOpen(false), []);
  const deleteMutation = useDeleteExamConfig(decodeId(ucId));
  const downloadMutation = useDownloadExamConfig();

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
          <Badge variant={statusConfig[examConfig.status].variant}>
            {statusConfig[examConfig.status].label}
          </Badge>
          <div className="w-px h-8 bg-border" />
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

        {examConfig.status === "COMPLETED" && (
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.stopPropagation();
              downloadMutation.mutate(id);
            }}
            disabled={downloadMutation.isPending}
            className="cursor-pointer shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:text-primary hover:bg-primary/10 rounded-full"
          >
            <DownloadIcon className="h-4 w-4" />
          </Button>
        )}

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => e.stopPropagation()}
              className="cursor-pointer shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:text-red-500 hover:bg-red-50 rounded-full"
            >
              <Trash2Icon className="h-4 w-4" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                <Trash2Icon />
              </AlertDialogMedia>
              <AlertDialogTitle>Apagar Configuração de Exame</AlertDialogTitle>
              <AlertDialogDescription>
                Esta ação irá apagar permanentemente a configuração de exame.
                Deseja continuar?
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
                onClick={() => deleteMutation.mutate(id)}
              >
                Apagar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Card>

      {isModalOpen && (
        <Dialog open={isModalOpen} onOpenChange={handleCloseModal}>
          <DialogContent className="max-w-lg p-0 overflow-y-auto max-h-[90vh]">
            <ExamConfigCard examConfigData={examConfig} />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
