import { ExamConfigCard } from "@/components/novo-exame-steps/exam-config-card";
import type { ExamConfigI } from "@/lib/types";

const MOCK_EXAM_CONFIG: ExamConfigI = {
  id: 1,
  subject_id: 1,
  fraction: 25,
  num_variations: 3,
  num_versions: 2,
  status: "COMPLETED",
  topic_configs: Array.from({ length: 10 }, (_, i) => ({
    topic_id: i + 1,
    topic_name: `Tópico ${i + 1}`,
    num_questions: 3 + (i % 3),
    relative_weight: 1 + (i % 4),
  })),
};

export default function Step1Content({
  examConfig,
}: {
  examConfig?: ExamConfigI;
}) {
  return (
    <div className="shrink-0 overflow-y-auto custom-scrollbar max-h-[82vh]">
      <ExamConfigCard examConfigData={examConfig ?? MOCK_EXAM_CONFIG} />
    </div>
  );
}
