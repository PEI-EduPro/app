import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff } from "lucide-react";
import type { OptionKey, QuestionsI } from "@/lib/types";

type Grid = Record<number, Record<OptionKey, boolean>>;
const OPTIONS: OptionKey[] = ["a", "b", "c", "d"];

const MOCK_QUESTIONS: QuestionsI[] = [
  {
    question_number: 0,
    correct_answer: "b",
    discount: 25,
    value: 2,
    answers: { a: false, b: true, c: false, d: false },
  },
  {
    question_number: 1,
    correct_answer: "a",
    discount: 25,
    value: 2,
    answers: { a: true, b: false, c: false, d: false },
  },
  {
    question_number: 2,
    correct_answer: "c",
    discount: 25,
    value: 2,
    answers: { a: false, b: false, c: false, d: true },
  },
  {
    question_number: 3,
    correct_answer: "d",
    discount: 25,
    value: 2,
    answers: { a: false, b: false, c: true, d: false },
  },
];

const MOCK_EXAMS = Array.from({ length: 30 }, (_, i) => ({
  exam_id: 201 + i,
  corrected: i < 25,
  validated: i < 10,
  grade: i < 25 ? Math.round((10 + Math.random() * 10) * 100) / 100 : null,
  questions: i < 25 ? MOCK_QUESTIONS : null,
}));

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

export default function Step7Content() {
  const [selected, setSelected] = useState<number | null>(null);
  const [exams, setExams] = useState(MOCK_EXAMS);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [validated, setValidated] = useState(false);

  function handleSelect(examId: number) {
    const exam = exams.find((e) => e.exam_id === examId);
    if (!exam?.questions) return;
    setSelected(examId);
    setGrid(buildGrid(exam.questions));
    setGrade(exam.grade);
    setValidated(exam.validated);
  }

  function handleValidate() {
    if (!selected || !grid) return;
    setValidated(true);
    setExams((prev) =>
      prev.map((e) => (e.exam_id === selected ? { ...e, validated: true } : e)),
    );
  }

  const selectedExam = exams.find((e) => e.exam_id === selected);

  return (
    <div className="flex gap-4">
      <ul className="w-40 border-r flex flex-col gap-1 p-2 shrink-0 overflow-y-auto custom-scrollbar max-h-[82vh]">
        {exams.map((exam) => (
          <li key={exam.exam_id}>
            <Button
              disabled={!exam.corrected}
              variant={selected === exam.exam_id ? "secondary" : "ghost"}
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
        {selected !== null && selectedExam?.questions && grid ? (
          <div className="flex flex-col gap-6 w-full">
            <AnswerGrid
              questions={selectedExam.questions}
              grid={grid}
              onGridChange={setGrid}
              onGradeChange={setGrade}
              readOnly={validated}
            />
            {validated ? (
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
                  onClick={() => setValidated(false)}
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
                <Button
                  size="lg"
                  className="font-bold cursor-pointer"
                  onClick={handleValidate}
                >
                  Validar
                </Button>
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
