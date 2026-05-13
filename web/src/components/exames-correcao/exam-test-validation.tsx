import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useGetExamInfo } from "@/hooks/use-waiting-rooms";
import type { OptionKey, QuestionsI } from "@/lib/types";

const OPTIONS: OptionKey[] = ["a", "b", "c", "d"];

type Grid = Record<number, Record<OptionKey, boolean>>;

export function buildGrid(questions: QuestionsI[]): Grid {
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

export default function ExamTestValidation({
  examId,
  grade,
  grid,
  validated,
  onGridChange,
  onGradeChange,
  onValidate,
  onReCorrect,
  onExamLoaded,
}: {
  examId: number;
  grade: number | null;
  grid: Grid | null;
  validated: boolean;
  onGridChange: (grid: Grid) => void;
  onGradeChange: (grade: number) => void;
  onValidate: () => void;
  onReCorrect: () => void;
  onExamLoaded: (grade: number | null, grid: Grid, validated: boolean) => void;
}) {
  const { data: exam } = useGetExamInfo(examId);

  useEffect(() => {
    if (exam?.questions) {
      onExamLoaded(exam.grade ?? null, buildGrid(exam.questions), exam.validated);
    }
  }, [exam]);

  if (!exam?.questions || !grid) return null;

  return (
    <div className="flex flex-col gap-15 w-full">
      {exam.capture && (
        <img
          src={`data:image/jpeg;base64,${exam.capture}`}
          alt="Test example"
          className="h-fit object-contain rounded-md border"
        />
      )}
      <AnswerGrid
        questions={exam.questions ?? []}
        grid={grid}
        onGridChange={onGridChange}
        onGradeChange={onGradeChange}
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
            onClick={onReCorrect}
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
            onClick={onValidate}
          >
            Validar
          </Button>
        </div>
      )}
    </div>
  );
}
