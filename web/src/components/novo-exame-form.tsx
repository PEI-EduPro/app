import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import "@/components/ui/table";
import { CustomTable } from "./custom-table";
import { ExamConfigCard } from "./exam-config-card";
import { useAddExamConfig } from "@/hooks/use-exams";
import type { NewExamConfigI } from "@/lib/types";
import { useGetUCTopics } from "@/hooks/use-questions";

type TopicSelection = {
  id: string;
  nome: string;
};

export type NovoExameFormT = {
  topics: TopicSelection[];
  number_questions: Record<string, number>;
  relative_quotations: Record<string, number>;
  number_exams: number;
  fraction: number;
  exam_title: string;
  exam_date: string;
  semester: string;
  academic_year: string;
};

export const NovoExameForm = (props: {
  examData?: NovoExameFormT;
  ucID: number;
  ucName: string;
}) => {
  const { examData = null, ucID, ucName } = props;
  const [formStep, setFormStep] = useState<number>(0);
  const [validatedData, setValidatedData] = useState<NovoExameFormT | null>(
    null
  );
  const totalSteps = 5;
  const navigate = useNavigate();

  const { mutate, isPending } = useAddExamConfig();
  const { data: topics } = useGetUCTopics(ucID);

  const form = useForm<NovoExameFormT>({
    defaultValues: {
      topics: examData?.topics || [],
      number_questions: examData?.number_questions || {},
      relative_quotations: examData?.relative_quotations || {},
      number_exams: examData?.number_exams || 1,
      fraction: examData?.fraction || 0,
      exam_title: examData?.exam_title || "Exame Época Normal",
      exam_date: examData?.exam_date || new Date().toISOString().split('T')[0],
      semester: examData?.semester || "1",
      academic_year: examData?.academic_year || "2025/26",
    },
  });

  const { handleSubmit, control, reset, watch, setValue, getValues } = form;

  const validateAndNormalizeData = (
    formData: NovoExameFormT
  ): NovoExameFormT => {
    const validated: NovoExameFormT = {
      ...formData,
      number_exams:
        formData.number_exams && formData.number_exams >= 1
          ? formData.number_exams
          : 1,
      fraction:
        formData.fraction !== undefined &&
        formData.fraction >= 0 &&
        formData.fraction <= 100
          ? formData.fraction
          : 0,
      number_questions: { ...formData.number_questions },
      relative_quotations: { ...formData.relative_quotations },
    };

    formData.topics?.forEach((topic) => {
      const currentNumQuestions = validated.number_questions[topic.id];
      if (
        !currentNumQuestions ||
        currentNumQuestions < 1 ||
        isNaN(currentNumQuestions)
      ) {
        validated.number_questions[topic.id] = 1;
      }

      const currentRelQuotation = validated.relative_quotations[topic.id];
      if (
        !currentRelQuotation ||
        currentRelQuotation < 1 ||
        isNaN(currentRelQuotation)
      ) {
        validated.relative_quotations[topic.id] = 1;
      }
    });

    return validated;
  };

  const handleNextStep = () => {
    const currentStep = formStep;
    const formData = getValues();

    if (currentStep === 3) {
      const validated = validateAndNormalizeData(formData);
      setValidatedData(validated);

      setValue("number_exams", validated.number_exams);
      setValue("fraction", validated.fraction);

      Object.keys(validated.number_questions).forEach((key) => {
        setValue(`number_questions.${key}`, validated.number_questions[key]);
      });

      Object.keys(validated.relative_quotations).forEach((key) => {
        setValue(
          `relative_quotations.${key}`,
          validated.relative_quotations[key]
        );
      });
    }

    setFormStep(currentStep + 1);
  };

  const handlePreviousStep = () => {
    setFormStep(formStep - 1);
  };

  const onSubmit = async (formData: NovoExameFormT) => {
    const finalData = validatedData || validateAndNormalizeData(formData);

    const novoExameData: NewExamConfigI = {
      subject_id: ucID,
      topics: finalData.topics.map((topic) => topic.nome),
      fraction: finalData.fraction,
      num_variations: finalData.number_exams,
      number_questions: {},
      relative_quotations: {},
      exam_title: finalData.exam_title,
      exam_date: finalData.exam_date,
      semester: finalData.semester,
      academic_year: finalData.academic_year,
    };

    finalData.topics.forEach((topic) => {
      const topicNome = topic.nome;
      if (topicNome) {
        novoExameData.number_questions[topicNome] =
          finalData.number_questions[topic.id];
        novoExameData.relative_quotations[topicNome] =
          finalData.relative_quotations[topic.id];
      }
    });

    const loadingToast = toast.loading("A gerar exames...");

    mutate(novoExameData, {
      onSuccess: () => {
        toast.dismiss(loadingToast);
        toast.success("Exame criado com sucesso!");
        setFormStep(0);
        setValidatedData(null);
        reset();
        navigate({ to: "/detalhes-uc", search: { ucId: ucID } });
      },
      onError: (error) => {
        toast.dismiss(loadingToast);
        toast.error(`Erro ao gerar exame: ${error.message}`);
      },
    });
  };

  const getDisplayData = () => {
    const formData =
      formStep === 4 && validatedData ? validatedData : getValues();

    return {
      id: 0, // dummy id for display purposes
      subject_id: ucID,
      fraction: formData.fraction,
      num_variations: formData.number_exams,
      topic_configs: formData.topics.map((topic) => ({
        topic_id: parseInt(topic.id),
        topic_name: topic.nome,
        number_questions: formData.number_questions[topic.id] || 1,
        relative_weight: formData.relative_quotations[topic.id] || 1,
      })),
    };
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-center">
        {Array.from({ length: totalSteps }).map((_, index) => (
          <div key={index} className="flex items-center">
            <div
              className={cn(
                "w-4 h-4 rounded-full transition-all duration-300 ease-in-out",
                index <= formStep ? "bg-primary" : "bg-primary/30",
                index < formStep && "bg-primary"
              )}
            />
            {index < totalSteps - 1 && (
              <div
                className={cn(
                  "w-8 h-0.5",
                  index < formStep ? "bg-primary" : "bg-primary/30"
                )}
              />
            )}
          </div>
        ))}
      </div>
      <Card className="border-none shadow-none">
        <CardContent>
          {formStep === 0 && (
            // Selecionar tópicos
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <FormField
                  control={control}
                  name="topics"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-center block text-lg">
                        Tópicos
                      </FormLabel>
                      {topics && (
                        <CustomTable
                          isSelectable
                          data={topics.map((topic) => ({
                            id: topic[0].id.toString(),
                            nome: topic[0].name,
                          }))}
                          onChange={field.onChange}
                          rowSelection={field.value}
                        />
                      )}
                    </FormItem>
                  )}
                />

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="bg-white text-black font-medium"
                    variant="outline"
                    size="sm"
                    disabled
                  >
                    Retroceder
                  </Button>
                  <Button
                    disabled={!(watch("topics")?.length > 0)}
                    type="button"
                    size="sm"
                    className="font-medium"
                    onClick={handleNextStep}
                  >
                    Próximo
                  </Button>
                </div>
              </form>
            </Form>
          )}

          {formStep === 1 && (
            // Selecionar número de questões por módulo
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <div className="space-y-4">
                  <FormLabel className="text-center block text-lg">
                    Número de questões por tópico
                  </FormLabel>

                  {watch("topics")?.map((topic) => {
                    const maxQuestions = topics
                      ?.map((t) =>
                        t[0].id.toString() === topic.id ? t[1] : 0
                      )
                      .filter((n) => n !== 0)[0] || 1;
                    
                    return (
                    <FormItem
                      key={topic.id}
                      className="flex items-center gap-x-4"
                    >
                      <FormLabel className="flex-shrink-0 w-140">
                        {topic.nome} (max: {maxQuestions})
                      </FormLabel>
                      <FormControl className="flex-1">
                        <Input
                          type="number"
                          min="1"
                          max={maxQuestions}
                          placeholder="1"
                          value={watch(`number_questions.${topic.id}`) || ""}
                          onChange={(e) => {
                            const value = e.target.value;

                            // Allow empty value for backspacing
                            if (value === "") {
                              setValue(`number_questions.${topic.id}`, NaN);
                              return;
                            }

                            const numValue = parseInt(value);
                            const clampedValue = Math.min(Math.max(isNaN(numValue) ? 1 : numValue, 1), maxQuestions);
                            setValue(`number_questions.${topic.id}`, clampedValue);
                          }}
                          onBlur={(e) => {
                            const value = e.target.value;

                            // Only validate and set to 1 on blur if empty
                            if (value === "") {
                              setValue(`number_questions.${topic.id}`, 1);
                              return;
                            }

                            const numValue = parseInt(value);
                            const clampedValue = Math.min(Math.max(isNaN(numValue) ? 1 : numValue, 1), maxQuestions);
                            setValue(`number_questions.${topic.id}`, clampedValue);
                          }}
                          onKeyDown={(e) => {
                            if (
                              !/[0-9]/.test(e.key) &&
                              ![
                                "Backspace",
                                "Delete",
                                "Tab",
                                "Escape",
                                "Enter",
                                "ArrowLeft",
                                "ArrowRight",
                                "ArrowUp",
                                "ArrowDown",
                                "Home",
                                "End",
                              ].includes(e.key) &&
                              !e.ctrlKey &&
                              !e.metaKey
                            ) {
                              e.preventDefault();
                            }
                          }}
                        />
                      </FormControl>
                    </FormItem>
                  )})}
                </div>
                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="bg-white text-black font-medium"
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousStep}
                  >
                    Retroceder
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="font-medium"
                    onClick={handleNextStep}
                  >
                    Próximo
                  </Button>
                </div>
              </form>
            </Form>
          )}

          {formStep === 2 && (
            // Selecionar cotações relativas e número de exames
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <div className="space-y-4">
                  <FormLabel className="text-center block text-lg">
                    Cotações relativas por tópico
                  </FormLabel>
                  {watch("topics")?.map((topic) => (
                    <FormItem
                      key={topic.id}
                      className="flex items-center gap-x-4"
                    >
                      <FormLabel className="flex-shrink-0 w-140">
                        {topic.nome}
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          placeholder="1"
                          value={watch(`relative_quotations.${topic.id}`) || ""}
                          onChange={(e) => {
                            const value = e.target.value;

                            // Allow empty value for backspacing
                            if (value === "") {
                              setValue(`relative_quotations.${topic.id}`, NaN);
                              return;
                            }

                            const numValue = parseInt(value);
                            setValue(
                              `relative_quotations.${topic.id}`,
                              isNaN(numValue) || numValue < 1 ? 1 : numValue
                            );
                          }}
                          onBlur={(e) => {
                            const value = e.target.value;

                            // Only validate and set to 1 on blur if empty
                            if (value === "") {
                              setValue(`relative_quotations.${topic.id}`, 1);
                              return;
                            }

                            const numValue = parseInt(value);
                            if (isNaN(numValue) || numValue < 1) {
                              setValue(`relative_quotations.${topic.id}`, 1);
                            }
                          }}
                          onKeyDown={(e) => {
                            if (
                              !/[0-9]/.test(e.key) &&
                              ![
                                "Backspace",
                                "Delete",
                                "Tab",
                                "Escape",
                                "Enter",
                                "ArrowLeft",
                                "ArrowRight",
                                "ArrowUp",
                                "ArrowDown",
                                "Home",
                                "End",
                              ].includes(e.key) &&
                              !e.ctrlKey &&
                              !e.metaKey
                            ) {
                              e.preventDefault();
                            }
                          }}
                        />
                      </FormControl>
                    </FormItem>
                  ))}

                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2">
                      Como funcionam as cotações relativas?
                    </h4>
                    <p className="text-sm text-blue-700">
                      As <span className="font-medium">cotações relativas</span>{" "}
                      determinam o peso de cada tópico no exame.<br></br>
                      Quanto maior a cotação de um tópico, maior será a sua
                      importância na nota final.
                    </p>
                  </div>
                </div>

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="bg-white text-black font-medium"
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousStep}
                  >
                    Retroceder
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="font-medium"
                    onClick={handleNextStep}
                  >
                    Próximo
                  </Button>
                </div>
              </form>
            </Form>
          )}

          {formStep === 3 && (
            // Final step: Number of exams and discount
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <div className="space-y-4">
                  <FormLabel className="text-center block text-lg">
                    Configurações finais
                  </FormLabel>

                  {/* Exam title field */}
                  <FormField
                    control={control}
                    name="exam_title"
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Título do exame
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="text"
                            placeholder="Ex: Teste Teórico 1"
                            {...field}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  {/* Exam date field */}
                  <FormField
                    control={control}
                    name="exam_date"
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Data do exame
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="date"
                            {...field}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  {/* Semester field */}
                  <FormField
                    control={control}
                    name="semester"
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Semestre
                        </FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione o semestre" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="1">1º Semestre</SelectItem>
                            <SelectItem value="2">2º Semestre</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />

                  {/* Academic year field */}
                  <FormField
                    control={control}
                    name="academic_year"
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Ano letivo
                        </FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione o ano" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="2024/25">2024/25</SelectItem>
                            <SelectItem value="2025/26">2025/26</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />

                  <hr />

                  {/* Number of exams field */}
                  <FormField
                    control={control}
                    name="number_exams"
                    render={() => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Número de exames
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min="1"
                            placeholder="1"
                            value={watch(`number_exams`) || ""}
                            onChange={(e) => {
                              const value = e.target.value;

                              // Allow empty value for backspacing
                              if (value === "") {
                                setValue(`number_exams`, NaN);
                                return;
                              }

                              const numValue = parseInt(value);
                              setValue(
                                `number_exams`,
                                isNaN(numValue) || numValue < 1 ? 1 : numValue
                              );
                            }}
                            onBlur={(e) => {
                              const value = e.target.value;

                              // Only validate and set to 1 on blur if empty
                              if (value === "") {
                                setValue(`number_exams`, 1);
                                return;
                              }

                              const numValue = parseInt(value);
                              if (isNaN(numValue) || numValue < 1) {
                                setValue(`number_exams`, 1);
                              }
                            }}
                            onKeyDown={(e) => {
                              if (
                                !/[0-9]/.test(e.key) &&
                                ![
                                  "Backspace",
                                  "Delete",
                                  "Tab",
                                  "Escape",
                                  "Enter",
                                  "ArrowLeft",
                                  "ArrowRight",
                                  "ArrowUp",
                                  "ArrowDown",
                                  "Home",
                                  "End",
                                ].includes(e.key) &&
                                !e.ctrlKey &&
                                !e.metaKey
                              ) {
                                e.preventDefault();
                              }
                            }}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  <hr />

                  {/* Discount field */}
                  <FormField
                    control={control}
                    name="fraction"
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Desconto (%)
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min="0"
                            max="100"
                            placeholder="0"
                            value={field.value || ""}
                            onChange={(e) => {
                              let value = parseInt(e.target.value);

                              if (isNaN(value)) {
                                field.onChange(0);
                                return;
                              }

                              value = Math.max(0, Math.min(100, value));
                              field.onChange(value);
                            }}
                            onBlur={(e) => {
                              const value = parseInt(e.target.value);
                              if (isNaN(value)) {
                                field.onChange(0);
                              }
                            }}
                            onKeyDown={(e) => {
                              if (
                                !/[0-9]/.test(e.key) &&
                                ![
                                  "Backspace",
                                  "Delete",
                                  "Tab",
                                  "Escape",
                                  "Enter",
                                  "ArrowLeft",
                                  "ArrowRight",
                                  "ArrowUp",
                                  "ArrowDown",
                                  "Home",
                                  "End",
                                ].includes(e.key) &&
                                !e.ctrlKey &&
                                !e.metaKey
                              ) {
                                e.preventDefault();
                              }
                            }}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <h4 className="font-semibold text-amber-800 mb-2">
                      Sobre o desconto
                    </h4>
                    <p className="text-sm text-amber-700">
                      Para cada questão errada, será descontado{" "}
                      <span className="font-bold">
                        {getDisplayData().fraction || 0}%
                      </span>{" "}
                      do valor da questão.<br></br>
                      Exemplo: Se uma questão vale 2 valores e o desconto é de
                      20%, cada erro nessa questão resulta numa penalização de
                      0.4 valores.
                    </p>
                  </div>
                </div>

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="bg-white text-black font-medium"
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousStep}
                  >
                    Retroceder
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="font-medium"
                    onClick={handleNextStep}
                  >
                    Próximo
                  </Button>
                </div>
              </form>
            </Form>
          )}

          {formStep === 4 && (
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <div className="space-y-6">
                  <FormLabel className="text-center block text-2xl font-bold text-primary">
                    Resumo do Exame
                  </FormLabel>
                  <ExamConfigCard examConfigData={getDisplayData()} />
                </div>

                <div className="flex justify-between pt-4">
                  <Button
                    type="button"
                    className="bg-white text-black font-medium"
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousStep}
                  >
                    Retroceder
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="font-medium"
                    disabled={isPending}
                    onClick={() => {
                      handleSubmit(onSubmit)();
                    }}
                  >
                    {isPending ? "A gerar..." : "Gerar Exame"}
                  </Button>
                </div>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
