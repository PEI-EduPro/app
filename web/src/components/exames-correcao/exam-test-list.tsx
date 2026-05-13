import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useGetExamsResponses } from "@/hooks/use-waiting-rooms";

function StatusIndicator({
  corrected,
  validated,
}: {
  corrected: boolean;
  validated: boolean;
}) {
  if (!corrected)
    return <span className="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0" />;
  return (
    <span className="flex items-center gap-2 shrink-0">
      <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
      <span>{validated ? <Eye size={12} /> : <EyeOff size={12} />}</span>
    </span>
  );
}

export default function ExamTestList({
  wrId,
  selected,
  onSelect,
}: {
  wrId: number;
  selected: number | null;
  onSelect: (examId: number) => void;
}) {
  const { data: examsResponses } = useGetExamsResponses(wrId, 5000);

  return (
    <ul className="w-48 border-r flex flex-col gap-1 p-2 overflow-y-auto custom-scrollbar shrink-0">
      {[...(examsResponses ?? [])]
        .sort((a, b) => {
          const rank = (e: typeof a) =>
            e.corrected && !e.validated
              ? 0
              : e.corrected && e.validated
                ? 1
                : 2;
          return rank(a) - rank(b);
        })
        .map((exam) => (
          <li key={exam.exam_id}>
            <Button
              disabled={!exam.corrected}
              variant={selected === exam.exam_id ? "secondary" : "ghost"}
              className="w-full justify-between cursor-pointer"
              onClick={() => onSelect(exam.exam_id)}
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
  );
}
