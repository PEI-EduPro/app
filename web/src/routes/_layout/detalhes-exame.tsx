import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { decodeId } from "@/lib/id-encoder";
import { StepItem } from "@/components/detalhes-exam/step-item";
import Step1Content from "@/components/detalhes-exam/step1-configuracao-criacao";
import Step2Content from "@/components/detalhes-exam/step2-inicio-exame";
import Step4Content from "@/components/detalhes-exam/step4-fecho-exame";
import Step6Content from "@/components/detalhes-exam/step6-correcao-associacao";
import Step7Content from "@/components/detalhes-exam/step7-validacao-correcao";
import Step8Content from "@/components/detalhes-exam/step8-lancamento-notas";
import { useGetExamConfig } from "@/hooks/use-exams";
import { CheckCircle2, XCircle, Clock } from "lucide-react";

const searchSchema = z.object({
  examId: z.string(),
  examName: z.string(),
  ucId: z.string(),
  ucName: z.string(),
});

export const Route = createFileRoute("/_layout/detalhes-exame")({
  validateSearch: searchSchema,
  component: RouteComponent,
});

function RouteComponent() {
  const { examId, examName, ucId, ucName } = Route.useSearch();
  const realExamId = decodeId(examId);
  const realUcId = decodeId(ucId);

  const { data: examConfigs } = useGetExamConfig(realUcId);
  const examConfig = examConfigs?.find((c) => c.id === realExamId);

  const steps = [
    {
      label: "Configuração e Criação do Exame",
      description: <Step1Content examConfig={examConfig} />,
      action: <CheckCircle2 className="h-6 w-6 text-green-500" />,
      hint: "Visualização da configuração do exame (número de variantes, versões, desconto por resposta errada e distribuição de questões por tópico) e transferência de zip com testes e ficheiro de respostas.",
    },
    {
      label: "Início do Exame",
      description: <Step2Content />,
      action: <CheckCircle2 className="h-6 w-6 text-green-500" />,
      hint: "Inicia o exame e abre a sala de espera para os alunos. Defina os vigilantes antes de iniciar.",
    },
    {
      label: "Associação Exame-Aluno",
      action: (
        <span className="text-sm font-semibold text-muted-foreground">
          25/100
        </span>
      ),
      hint: "Realizada exclusivamente na aplicação móvel. Os vigilantes associam cada aluno ao respetivo exame físico. O número indica os alunos já associados.",
    },
    {
      label: "Termino do Exame",
      description: <Step4Content />,
      action: <CheckCircle2 className="h-6 w-6 text-green-500" />,
      hint: "Termina o exame e fecha a sala de espera. Pode ser feito na aplicação móvel ou aqui.",
    },
    {
      label: "Captura e Upload dos Exames",
      action: (
        <span className="text-sm font-semibold text-muted-foreground">
          25/100
        </span>
      ),
      hint: "Realizada exclusivamente na aplicação móvel. Os vigilantes fotografam e fazem upload das folhas de resposta. O número indica os exames já carregados.",
    },
    {
      label: "Correção de Problemas de Associação",
      description: <Step6Content />,
      action: <XCircle className="h-6 w-6 text-red-500" />,
      hint: "Resolução manual de casos em que a associação entre aluno e exame falhou ou ficou ambígua.",
    },
    {
      label: "Validação Manual da Correção",
      description: <Step7Content />,
      action: <Clock className="h-6 w-6 text-yellow-500" />,
      hint: "Revisão e validação manual das correções automáticas antes de lançar as notas.",
    },
    {
      label: "Lançamento de Notas",
      description: <Step8Content />,
      action: <Clock className="h-6 w-6 text-yellow-500" />,
      hint: "Envio das notas finais por email para os alunos. Configure o conteúdo do email, lance as notas e tranfira um pdf com as notas.",
    },
  ];

  return (
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-4 md:px-6 w-full">
      <AppBreadcrumb
        page={examName}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
          { name: ucName, link: `/detalhes-uc?ucId=${ucId}` },
        ]}
      />

      <div className="overflow-y-auto overflow-x-hidden custom-scrollbar flex-1">
        <div className="w-full md:px-47.5">
          <h1 className="font-rubik typography-h1 text-center mb-10">
            {examName}
          </h1>

          <div className="flex flex-col">
            {steps.map((step, i) => (
              <StepItem
                key={i}
                step={step}
                index={i}
                isLast={i === steps.length - 1}
                noExpand={i === 2 || i === 4}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
