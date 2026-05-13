import { useState } from "react";
import {
  useCorrectExam,
  useGetExamsResponses,
  useGetWarnings,
  useValidateExam,
} from "@/hooks/use-waiting-rooms";
import ExamTestList from "@/components/exames-correcao/exam-test-list";
import ExamTestValidation from "@/components/exames-correcao/exam-test-validation";
import PostGradesModal from "@/components/exames-correcao/post-grades-modal";
import { Button } from "@/components/ui/button";
import type { OptionKey } from "@/lib/types";

type Grid = Record<number, Record<OptionKey, boolean>>;

export default function ExamsCorrectionValidation({ wrId }: { wrId: number }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [validated, setValidated] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const { data: examsResponses } = useGetExamsResponses(wrId);
  const { data: warningsErrors } = useGetWarnings(wrId);
  const { mutate: validateExam } = useValidateExam(wrId);
  const { mutate: correctExam } = useCorrectExam(wrId);

  const allValidated =
    !!examsResponses?.length &&
    examsResponses.every((e) => e.validated) &&
    (warningsErrors?.warnings?.length ?? 0) === 0;

  function handleSelect(examId: number) {
    setSelected(examId);
    setGrid(null);
  }

  function handleExamLoaded(
    loadedGrade: number | null,
    loadedGrid: Grid,
    loadedValidated: boolean,
  ) {
    setGrade(loadedGrade);
    setGrid(loadedGrid);
    setValidated(loadedValidated);
  }

  function handleValidate() {
    if (!selected) return;
    setValidated(true);
    validateExam(selected);
    if (grid) correctExam({ examId: selected, props: { grid } });
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="shrink-0 p-2">
        <Button
          disabled={!allValidated}
          className="cursor-pointer"
          onClick={() => setModalOpen(true)}
        >
          Lançar notas
        </Button>
      </div>

      <PostGradesModal
        wrId={wrId}
        open={modalOpen}
        onOpenChange={setModalOpen}
      />

      <div className="flex flex-1 min-h-0">
        <ExamTestList wrId={wrId} selected={selected} onSelect={handleSelect} />

        <div className="flex-1 px-6 flex items-start min-w-0">
          {selected !== null ? (
            <ExamTestValidation
              examId={selected}
              grade={grade}
              grid={grid}
              validated={validated}
              onGridChange={setGrid}
              onGradeChange={setGrade}
              onValidate={handleValidate}
              onReCorrect={() => setValidated(false)}
              onExamLoaded={handleExamLoaded}
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              Selecione um teste para corrigir.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
