import { ExamConfigCard } from "@/components/novo-exame-steps/exam-config-card";
import type { ExamConfigI } from "@/lib/types";

export default function Step1Content({
  examConfig,
}: {
  examConfig: ExamConfigI;
}) {
  return (
    <div className="shrink-0 overflow-y-auto custom-scrollbar max-h-[82vh]">
      <ExamConfigCard examConfigData={examConfig} />
    </div>
  );
}
