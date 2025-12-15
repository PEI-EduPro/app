import type { ExamConfigI } from "@/lib/types";
import { Card, CardContent } from "./ui/card";

export function ExamConfigCard({
  examConfigData,
}: {
  examConfigData: ExamConfigI;
}) {
  const { fraction, num_variations, topic_configs } = examConfigData;
  return (
    <Card className="border-2 border-primary/20 bg-primary/5">
      <CardContent className="px-6">
        <div className="mb-6 pb-4 border-b">
          <h3 className="text-lg font-semibold text-center mb-3">
            Configuração Geral
          </h3>
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="p-3 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-muted-foreground">Exames a gerar</p>
              <p className="text-2xl font-bold text-primary">
                {num_variations || 1}
              </p>
            </div>
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
            {topic_configs?.map((topic) => {
              const numQuestions = topic.number_questions || 1;
              const relativeQuotation = topic.relative_weight || 1;

              return (
                <div
                  key={topic.topic_id}
                  className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
                >
                  <div>
                    <p className="font-medium">{topic.topic_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {numQuestions} pergunta
                      {numQuestions !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-primary">
                      Cotação relativa: {relativeQuotation}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div className="pt-4 border-t">
          <div className="flex justify-between text-center items-center">
            <div>
              <p className="text-sm text-muted-foreground">Total de questões</p>
              <p className="text-xl font-bold">
                {topic_configs
                  ?.reduce(
                    (total, topic) => total + (topic.number_questions || 1),
                    0
                  )
                  .toString() || "0"}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
