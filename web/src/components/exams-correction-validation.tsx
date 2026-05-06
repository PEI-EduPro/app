import { useState } from "react";
import {
  useCorrectExam,
  useGetExamsResponses,
  useValidateExam,
} from "@/hooks/use-waiting-rooms";
import ExamTestList from "@/components/exam-test-list";
import ExamTestValidation from "@/components/exam-test-validation";
import type { OptionKey } from "@/lib/types";

type Grid = Record<number, Record<OptionKey, boolean>>;

export default function ExamsCorrectionValidation({ wrId }: { wrId: number }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [validated, setValidated] = useState(false);

  useGetExamsResponses(wrId);
  const { mutate: validateExam } = useValidateExam(wrId);
  const { mutate: correctExam } = useCorrectExam(wrId);

  function handleSelect(examId: number) {
    setSelected(examId);
    setGrid(null);
  }

  function handleExamLoaded(loadedGrade: number | null, loadedGrid: Grid, loadedValidated: boolean) {
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
    <div className="flex h-full min-h-0">
      <ExamTestList wrId={wrId} selected={selected} onSelect={handleSelect} />

      <div className="flex-1 p-6 flex items-start min-w-0">
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
  );
}
