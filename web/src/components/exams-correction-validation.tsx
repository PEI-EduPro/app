import { useState } from "react";
import {
  useCorrectExam,
  useGetExamsResponses,
  useValidateExam,
} from "@/hooks/use-waiting-rooms";
import ExamTestList from "@/components/exam-test-list";
import ExamTestValidation, {
  buildGrid,
} from "@/components/exam-test-validation";
import type { OptionKey } from "@/lib/types";

type Grid = Record<number, Record<OptionKey, boolean>>;

export default function ExamsCorrectionValidation({ wrId }: { wrId: number }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [validated, setValidated] = useState(false);

  const { data: examsResponses } = useGetExamsResponses(wrId);
  const { mutate: validateExam } = useValidateExam(wrId);
  const { mutate: correctExam } = useCorrectExam(wrId);

  const selectedExam = examsResponses?.find((e) => e.exam_id === selected);

  function handleSelect(examId: number) {
    setSelected(examId);
    const exam = examsResponses?.find((e) => e.exam_id === examId);
    setGrade(exam?.grade ?? null);
    setGrid(exam?.questions ? buildGrid(exam.questions) : null);
    setValidated(exam?.validated ?? false);
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
        {selectedExam?.questions ? (
          <ExamTestValidation
            exam={selectedExam}
            grade={grade}
            grid={grid ?? buildGrid(selectedExam.questions)}
            validated={validated}
            onGridChange={setGrid}
            onGradeChange={setGrade}
            onValidate={handleValidate}
            onReCorrect={() => setValidated(false)}
          />
        ) : (
          <p className="text-sm text-muted-foreground">
            {!selected && "Selecione um teste para corrigir."}
          </p>
        )}
      </div>
    </div>
  );
}
