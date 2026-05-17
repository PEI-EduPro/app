import type { GetTopicI, NewExamConfigI, ExamConfigI } from "@/lib/types";
import { Card, CardContent } from "../ui/card";

type ExamConfigCardData = NewExamConfigI | ExamConfigI;

function isNewExamConfig(data: ExamConfigCardData): data is NewExamConfigI {
  return "topics" in data;
}

export function ExamConfigCard({
  examConfigData,
  allTopics = [],
}: {
  examConfigData: ExamConfigCardData;
  allTopics?: GetTopicI[];
}) {
  const fraction = examConfigData.fraction;
  const num_variations =
    "num_variations" in examConfigData
      ? examConfigData.num_variations
      : undefined;
  const num_versions =
    "num_versions" in examConfigData
      ? examConfigData.num_versions
      : undefined;

  // Normalise to a common list of { id, name, numQuestions, relativeQuotation }
  const topicRows = isNewExamConfig(examConfigData)
    ? (() => {
        const topicNames: Record<string, string> = Object.fromEntries(
          allTopics.map(([topic]) => [String(topic.id), topic.name]),
        );
        return (examConfigData.topics ?? []).map((id: string) => ({
          key: id,
          name: topicNames[id] ?? id,
          numQuestions: examConfigData.number_questions?.[Number(id)] || 1,
          relativeQuotation:
            examConfigData.relative_quotations?.[Number(id)] || 1,
        }));
      })()
    : examConfigData.topic_configs.map((tc) => ({
        key: String(tc.topic_id),
        name: tc.topic_name,
        numQuestions: tc.num_questions,
        relativeQuotation: tc.relative_weight,
      }));

  const totalQuestions = topicRows.reduce((sum, t) => sum + t.numQuestions, 0);

  return (
    <Card className="border-2 border-primary/20 bg-primary/5">
      <CardContent className="px-6">
        <div className="mb-6 pb-4 border-b">
          <h3 className="text-lg font-semibold text-center mb-3">
            Configuração Geral
          </h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            {num_variations !== undefined && (
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-sm text-muted-foreground">Exames a gerar</p>
                <p className="text-2xl font-bold text-primary">
                  {num_variations || 1}
                </p>
              </div>
            )}
            {num_versions !== undefined && (
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-sm text-muted-foreground">Versões</p>
                <p className="text-2xl font-bold text-primary">
                  {num_versions || 1}
                </p>
              </div>
            )}
            <div className="p-3 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-muted-foreground">Desconto</p>
              <p className="text-2xl font-bold text-primary">
                {fraction || 0}%
              </p>
            </div>
          </div>
        </div>
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Tópicos Selecionados</h3>
          <div className="space-y-2">
            {topicRows.map((topic) => (
              <div
                key={topic.key}
                className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
              >
                <div>
                  <p className="font-medium">{topic.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {topic.numQuestions} pergunta
                    {topic.numQuestions !== 1 ? "s" : ""}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-primary">
                    Cotação relativa: {topic.relativeQuotation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="pt-4 border-t">
          <div className="flex justify-between text-center items-center">
            <div>
              <p className="text-sm text-muted-foreground">Total de questões</p>
              <p className="text-xl font-bold">{totalQuestions}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
