import type { NovoExameFormT } from "./novo-exame-form";
import { Card, CardContent } from "./ui/card";

export function ExamConfigCard({
  examConfigData,
}: {
  examConfigData: NovoExameFormT;
}) {
  const {
    fraction,
    number_exams,
    number_questions,
    relative_quotations,
    topics,
  } = examConfigData;
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
                {number_exams || 1}
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
            {topics?.map((topic) => {
              const numQuestions = number_questions[topic.id] || 1;
              const relativeQuotation = relative_quotations[topic.id] || 1;

              return (
                <div
                  key={topic.id}
                  className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
                >
                  <div>
                    <p className="font-medium">{topic.nome}</p>
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
                {Object.values(number_questions || {}).reduce(
                  (sum, num) => sum + (num || 1),
                  0
                )}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
