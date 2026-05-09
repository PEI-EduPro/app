import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { usePostGrades } from "@/hooks/use-exams";

const TOGGLE_OPTIONS = [
  { key: "exam_capture", label: "Captura do exame" },
  { key: "question_weights", label: "Pesos das questões" },
  { key: "red_green_cross_table", label: "Tabela vermelho/verde" },
  { key: "cumulative_score_table", label: "Tabela de pontuação cumulativa" },
] as const;

type ToggleKey = (typeof TOGGLE_OPTIONS)[number]["key"];

export default function PostGradesModal({
  wrId,
  open,
  onOpenChange,
}: {
  wrId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { mutate: postGrades } = usePostGrades(wrId);
  const [options, setOptions] = useState<Record<ToggleKey, boolean>>({
    exam_capture: false,
    question_weights: false,
    red_green_cross_table: false,
    cumulative_score_table: false,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Lançar notas</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4 py-2">
          {TOGGLE_OPTIONS.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <Label htmlFor={key}>{label}</Label>
              <Switch
                id={key}
                checked={options[key]}
                onCheckedChange={(v) =>
                  setOptions((prev) => ({ ...prev, [key]: v }))
                }
              />
            </div>
          ))}
        </div>
        <DialogFooter
          className="
        !justify-start"
        >
          <Button
            className="cursor-pointer"
            onClick={() => {
              postGrades({ student_identification: true, ...options });
              onOpenChange(false);
            }}
          >
            Confirmar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
