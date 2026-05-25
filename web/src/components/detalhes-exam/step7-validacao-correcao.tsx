import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff } from "lucide-react";
import type { OptionKey, QuestionsI } from "@/lib/types";
import { useGetExamsResponses, useCorrectExam } from "@/hooks/use-exams";

type Grid = Record<number, Record<OptionKey, boolean>>;
const OPTIONS: OptionKey[] = ["a", "b", "c", "d"];

function buildGrid(questions: QuestionsI[]): Grid {
  return Object.fromEntries(
    questions.map((q) => [q.question_number, { ...q.answers }]),
  );
}

function calcGrade(grid: Grid, questions: QuestionsI[]) {
  let g = 0;
  questions.forEach((q) => {
    OPTIONS.forEach((opt) => {
      if (grid[q.question_number][opt]) {
        g += opt === q.correct_answer ? q.value : -q.value * (q.discount / 100);
      }
    });
  });
  return Math.max(0, Math.round(g * 100) / 100);
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
  onGridChange: (g: Grid) => void;
  onGradeChange: (g: number) => void;
  readOnly?: boolean;
}) {
  const correctAnswers = Object.fromEntries(
    questions.map((q) => [q.question_number, q.correct_answer]),
  );
  function toggle(id: number, opt: OptionKey) {
    const next = { ...grid, [id]: { ...grid[id], [opt]: !grid[id][opt] } };
    onGridChange(next);
    onGradeChange(calcGrade(next, questions));
  }
  return (
    <div className="overflow-auto w-full">
      <table className="border-collapse text-sm w-full">
        <thead>
          <tr>
            <th className="border border-border w-10 text-center font-medium text-muted-foreground p-1" />
            {questions.map((q) => (
              <th
                key={q.question_number}
                className="border border-border text-center font-medium text-muted-foreground p-1"
              >
                {q.question_number + 1}
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
              {questions.map((q) => (
                <td
                  key={q.question_number}
                  className={`border border-border p-1 ${correctAnswers[q.question_number] === opt ? "bg-green-200" : ""}`}
                >
                  <div className="flex items-center justify-center">
                    <input
                      type="checkbox"
                      checked={grid[q.question_number][opt]}
                      onChange={() =>
                        !readOnly && toggle(q.question_number, opt)
                      }
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

export default function Step7Content({
  examConfigId,
}: {
  examConfigId: number;
}) {
  const { data: exams = [] } = useGetExamsResponses(examConfigId);
  const { mutate: correctMutation, isPending: isCorrecting } =
    useCorrectExam(examConfigId);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [localValidated, setLocalValidated] = useState(false);

  function handleSelect(examId: number) {
    const exam = exams.find((e) => e.exam_id === examId);
    if (!exam?.questions) return;
    setSelectedId(examId);
    setGrid(buildGrid(exam.questions));
    setGrade(exam.grade);
    setLocalValidated(exam.validated);
  }

  function handleCorrect() {
    if (!selectedId || !grid) return;
    correctMutation(
      { examId: selectedId, props: { grid } },
      { onSuccess: () => setLocalValidated(true) },
    );
  }

  const selectedExam = exams.find((e) => e.exam_id === selectedId);

  return (
    <div className="flex gap-4">
      <ul className="w-40 border-r flex flex-col gap-1 p-2 shrink-0 overflow-y-auto custom-scrollbar max-h-[82vh]">
        {exams.map((exam) => (
          <li key={exam.batch_number}>
            <Button
              disabled={!exam.corrected}
              variant={selectedId === exam.exam_id ? "secondary" : "ghost"}
              className="w-full justify-between cursor-pointer"
              onClick={() => handleSelect(exam.exam_id)}
            >
              <span>Teste {exam.exam_id}</span>
              {exam.corrected ? (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  {exam.validated ? <Eye size={12} /> : <EyeOff size={12} />}
                </span>
              ) : (
                <span className="w-2 h-2 rounded-full bg-red-500" />
              )}
            </Button>
          </li>
        ))}
      </ul>

      <div className="flex-1 flex items-start">
        {selectedId !== null && selectedExam?.questions && grid ? (
          <div className="flex flex-col gap-6 w-full">
            {selectedExam.capture && (
              <img
                src={`data:image/jpeg;base64,${selectedExam.capture}`}
                alt="Test example"
                className="h-fit object-contain rounded-md border w-full max-h-50"
              />
            )}
            <AnswerGrid
              questions={selectedExam.questions}
              grid={grid}
              onGridChange={setGrid}
              onGradeChange={setGrade}
              readOnly={localValidated}
            />
            {localValidated ? (
              <div className="flex flex-col items-center gap-3 py-6 border rounded-xl bg-muted/40">
                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-extrabold text-primary">
                    {grade ?? 0}
                  </span>
                  <span className="text-xl text-muted-foreground">/ 20</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Este teste já foi corrigido.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="cursor-pointer"
                  onClick={() => setLocalValidated(false)}
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
                    {grade ?? 0}
                  </span>
                  <span className="text-sm text-muted-foreground">/ 20</span>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="lg"
                    className="font-bold cursor-pointer"
                    disabled={isCorrecting}
                    onClick={handleCorrect}
                  >
                    Guardar correção
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground pt-4">
            Selecione um teste para corrigir.
          </p>
        )}
      </div>
    </div>
  );
}
