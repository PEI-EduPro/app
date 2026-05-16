import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { useAddExamConfig } from "@/hooks/use-exams";
import { useGetUCTopics } from "@/hooks/use-questions";
import type { NewExamConfigI } from "@/lib/types";
import { Step0Topicos } from "./step0-topicos";
import { Step1NumQuestoes } from "./step1-num-questoes";
import { Step2Cotacoes } from "./step2-cotacoes";
import { Step3Configuracoes } from "./step3-configuracoes";
import { Step4VigilantesAlunos } from "./step4-vigilantes-alunos";
import { Step5Resumo } from "./step5-resumo";
import HelperHoverCard from "@/components/helper-hover-card";

const TOTAL_STEPS = 6;

const STEP_LABELS = [
  "Tópicos",
  "Questões",
  "Cotações",
  "Configurações",
  "Participantes",
  "Resumo",
];

export const NovoExameForm = ({
  ucID,
  onClose,
}: {
  ucID: number;
  onClose: () => void;
}) => {
  const [formStep, setFormStep] = useState(0);
  const [studentsCsv, setStudentsCsv] = useState<File | null>(null);
  const [selectedTopics, setSelectedTopics] = useState<
    { id: string; nome: string }[]
  >([]);

  const { mutate, isPending } = useAddExamConfig();
  const { data: topics } = useGetUCTopics(ucID);

  const form = useForm<NewExamConfigI>({
    mode: "onChange",
    defaultValues: {
      number_questions: {} as Record<number, number>,
      relative_quotations: {} as Record<number, number>,
      fraction: 0,
      exam_title: "",
    },
  });

  const onNext = () => setFormStep((s) => s + 1);
  const onPrev = () => setFormStep((s) => s - 1);

  const onSubmit = () => {
    toast.loading("A criar exame...", { position: "top-right" });
    const payload = { ...form.getValues(), subject_id: ucID };
    mutate(payload, {
      onSuccess: () => {
        setFormStep(0);
        form.reset();
        onClose();
      },
    });
  };

  const STEP_DESCRIPTIONS = [
    "Selecione os tópicos que farão parte do exame.",
    "Defina o número de questões a integrar de cada tópico.",
    "Configure o peso de cada tópico na nota final e o desconto por resposta errada.",
    "Defina o título, data, semestre e ano letivo do exame.",
    "Adicione os vigilantes, importe a lista de alunos e explicite o número de exames e versões.",
    "Reveja toda a configuração antes de gerar o exame.",
  ];

  const stepProps = { form, onNext, onPrev, onClose };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <Card
        className="flex flex-col flex-1 min-h-0 space-y-4 p-6 max-w-[calc(100vw/2.3)] h-[calc(100vh/1.2)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col mb-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-semibold">Novo Exame</h2>
            <Button
              variant="ghost"
              onClick={onClose}
              className="cursor-pointer"
            >
              <X className="h-6.25! w-6.25!" />
            </Button>
          </div>
          <div className="flex items-center justify-center">
            {Array.from({ length: TOTAL_STEPS }).map((_, index) => (
              <div key={index} className="flex items-center">
                <HelperHoverCard
                  side="top"
                  content={
                    <div className="text-xs">
                      <p className="font-semibold mb-1">{STEP_LABELS[index]}</p>
                      {STEP_DESCRIPTIONS[index]}
                    </div>
                  }
                  trigger={
                    <div
                      className={cn(
                        "w-4 h-4 rounded-full transition-all duration-300 ease-in-out cursor-default",
                        index <= formStep ? "bg-primary" : "bg-primary/30",
                      )}
                    />
                  }
                />
                {index < TOTAL_STEPS - 1 && (
                  <div
                    className={cn(
                      "w-8 h-0.5",
                      index < formStep ? "bg-primary" : "bg-primary/30",
                    )}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {formStep === 0 && (
          <Step0Topicos
            {...stepProps}
            topics={topics}
            selectedTopics={selectedTopics}
            setSelectedTopics={setSelectedTopics}
          />
        )}
        {formStep === 1 && (
          <Step1NumQuestoes
            {...stepProps}
            topics={topics}
            selectedTopics={selectedTopics}
          />
        )}
        {formStep === 2 && (
          <Step2Cotacoes {...stepProps} selectedTopics={selectedTopics} />
        )}
        {formStep === 3 && <Step3Configuracoes {...stepProps} />}
        {formStep === 4 && (
          <Step4VigilantesAlunos
            {...stepProps}
            studentsCsv={studentsCsv}
            setStudentsCsv={setStudentsCsv}
            isPending={isPending}
          />
        )}
        {formStep === 5 && (
          <Step5Resumo
            form={form}
            topics={topics}
            onPrev={onPrev}
            isPending={isPending}
            onSubmit={onSubmit}
          />
        )}
      </Card>
    </div>
  );
};
