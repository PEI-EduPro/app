import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useCorrectExam,
  useGetExamsResponses,
  useValidateExam,
} from "@/hooks/use-waiting-rooms";
import type { OptionKey, QuestionsI } from "@/lib/types";

const OPTIONS: OptionKey[] = ["a", "b", "c", "d"];

function StatusIndicator({
  corrected,
  validated,
}: {
  corrected: boolean;
  validated: boolean;
}) {
  if (!corrected) {
    return <span className="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0" />;
  }
  if (corrected) {
    return (
      <span className="flex items-center gap-2 shrink-0">
        <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
        <span>{validated ? <Eye size={12} /> : <EyeOff size={12} />}</span>
      </span>
    );
  }
  return null;
}

type Grid = Record<number, Record<OptionKey, boolean>>;

function buildGrid(questions: QuestionsI[]): Grid {
  const grid: Grid = {};
  questions.forEach((q) => {
    grid[q.question_number] = { ...q.answers };
  });
  return grid;
}

function calcGrade(grid: Grid, questions: QuestionsI[]): number {
  let grade = 0;
  questions.forEach((q) => {
    const selected = grid[q.question_number];
    OPTIONS.forEach((opt) => {
      if (selected[opt]) {
        if (opt === q.correct_answer) {
          grade += q.value;
        } else {
          grade -= q.value * (q.discount / 100);
        }
      }
    });
  });
  return Math.max(0, Math.round(grade * 100) / 100);
}

function AnswerGrid({
  questions,
  grid,
  onGridChange,
  onGradeChange,
  readOnly,
}: {
  questions: QuestionsI[];
  grid: Grid;
  onGridChange: (grid: Grid) => void;
  onGradeChange: (grade: number) => void;
  readOnly?: boolean;
}) {
  const questionIds = questions.map((q) => q.question_number);
  const correctAnswers = Object.fromEntries(
    questions.map((q) => [q.question_number, q.correct_answer]),
  );

  function toggle(questionId: number, opt: OptionKey) {
    const next = {
      ...grid,
      [questionId]: { ...grid[questionId], [opt]: !grid[questionId][opt] },
    };
    onGridChange(next);
    onGradeChange(calcGrade(next, questions));
  }

  return (
    <div className="overflow-auto w-full">
      <table className="border-collapse text-sm w-full">
        <thead>
          <tr>
            <th className="border border-border w-10 text-center font-medium text-muted-foreground p-1" />
            {questionIds.map((id) => (
              <th
                key={id}
                className="border border-border text-center font-medium text-muted-foreground p-1"
              >
                {id + 1}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {OPTIONS.map((opt) => (
            <tr key={opt}>
              <td className="border border-border text-center font-medium text-muted-foreground uppercase p-1">
                {opt}
              </td>
              {questionIds.map((id) => (
                <td
                  key={id}
                  className={`border border-border p-1 ${correctAnswers[id] === opt ? "bg-green-200 dark:bg-green-900" : ""}`}
                >
                  <div className="flex items-center justify-center">
                    <input
                      type="checkbox"
                      checked={grid[id][opt]}
                      onChange={() => !readOnly && toggle(id, opt)}
                      disabled={readOnly}
                      className="w-4 h-4 cursor-pointer accent-primary disabled:cursor-not-allowed"
                    />
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ExamsCorrectionValidation({ wrId }: { wrId: number }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [validated, setValidated] = useState(false);

  const { data: examsResponses } = useGetExamsResponses(wrId);
  const { mutate: validateExam } = useValidateExam(wrId);
  const { mutate: correctExam } = useCorrectExam(wrId);

  const selectedExam = examsResponses?.find((e) => e.exam_id === selected);

  function handleSelect(testId: number) {
    setSelected(testId);
    const exam = examsResponses?.find((e) => e.exam_id === testId);
    setGrade(exam?.grade ?? null);
    setGrid(exam?.questions ? buildGrid(exam.questions) : null);
    setValidated(exam?.validated ?? false);
  }

  function handleValidar(examId: number) {
    setValidated(true);
    validateExam(examId);
    if (grid) {
      correctExam({ examId, props: { exam_id: examId, grid } });
    }
  }

  function handleCorrigirOutraVez() {
    setValidated(false);
  }

  return (
    <div className="flex h-full min-h-0">
      <ul className="w-48 border-r flex flex-col gap-1 p-2 overflow-y-auto custom-scrollbar shrink-0">
        {examsResponses?.map((exam) => (
          <li key={exam.exam_id}>
            <Button
              disabled={!exam.corrected}
              variant={selected === exam.exam_id ? "secondary" : "ghost"}
              className="w-full justify-between cursor-pointer"
              onClick={() => handleSelect(exam.exam_id)}
            >
              <span>Teste {exam.exam_id}</span>
              <StatusIndicator
                corrected={exam.corrected}
                validated={exam.validated}
              />
            </Button>
          </li>
        ))}
      </ul>

      <div className="flex-1 p-6 flex items-start min-w-0">
        {selectedExam?.questions ? (
          <div className="flex flex-col gap-15 w-full">
            <img
              src={`data:image/jpeg;base64,${selectedExam.capture}`}
              alt="Test example"
              className="h-fit object-contain rounded-md border"
            />
            <AnswerGrid
              questions={selectedExam.questions}
              grid={grid ?? buildGrid(selectedExam.questions)}
              onGridChange={setGrid}
              onGradeChange={setGrade}
              readOnly={validated}
            />
            {validated ? (
              <div className="flex flex-col items-center gap-3 py-6 border rounded-xl bg-muted/40">
                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-extrabold text-primary">
                    {grade ? Math.round(grade * 100) / 100 : 0}
                  </span>
                  <span className="text-xl text-muted-foreground font-medium">
                    / 20
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Este teste já foi corrigido.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="cursor-pointer mt-1"
                  onClick={handleCorrigirOutraVez}
                >
                  Corrigir novamente
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between border rounded-xl px-5 py-3 bg-muted/40">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-sm font-semibold text-muted-foreground">
                    Nota:
                  </span>
                  <span className="text-3xl font-bold text-primary">
                    {grade ? Math.round(grade * 100) / 100 : 0}
                  </span>
                  <span className="text-sm text-muted-foreground">/ 20</span>
                </div>
                <Button
                  variant="default"
                  size="lg"
                  className="font-bold cursor-pointer"
                  onClick={() => selected && handleValidar(selected)}
                >
                  Validar
                </Button>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            {!selected && "Selecione um teste para corrigir."}
          </p>
        )}
      </div>
    </div>
  );
}
