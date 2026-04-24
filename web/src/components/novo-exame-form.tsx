import { useState } from "react";
import { useForm } from "react-hook-form";
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
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import "@/components/ui/table";
import { CustomTable } from "./custom-table";
import { ExamConfigCard } from "./exam-config-card";
import { useAddExamConfig } from "@/hooks/use-exams";
import type { NewExamConfigI } from "@/lib/types";
import { useGetUCTopics } from "@/hooks/use-questions";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { Calendar } from "./ui/calendar";
import { format, toDate } from "date-fns";
import HelperHoverCard from "./helper-hover-card";
import { useGetProfessors } from "@/hooks/use-users";
import { useKeycloak } from "@/hooks/use-keycloak";
import { MultiSelect } from "./multi-select";
import { Upload, X } from "lucide-react";

type TopicSelection = {
  id: string;
  nome: string;
};

export type NovoExameFormT = {
  fraction: number;
  exam_title: string;
  topics: TopicSelection[];
  number_questions: Record<string, number>;
  relative_quotations: Record<string, number>;
  number_exams: number;
  vigilantes: string[];
  exam_date: string;
  semester: string;
  academic_year: string;
  students_csv: File | null;
  number_versions: number;
};

export const NovoExameForm = (props: { ucID: number; onClose: () => void }) => {
  const { ucID, onClose } = props;
  const [formStep, setFormStep] = useState<number>(0);
  const [validatedData, setValidatedData] = useState<NovoExameFormT | null>(
    null,
  );
  const totalSteps = 6;

  const { mutate, isPending } = useAddExamConfig();
  const { data: topics } = useGetUCTopics(ucID);
  const { data: professors } = useGetProfessors();

  const keycloack = useKeycloak();

  const form = useForm<NovoExameFormT>({
    mode: "onChange",
  });

  const currentYear = new Date().getFullYear();
  const yearOptions = [
    `${currentYear - 1}/${String(currentYear).slice(-2)}`,
    `${currentYear}/${String(currentYear + 1).slice(-2)}`,
  ];

  const {
    handleSubmit,
    control,
    reset,
    watch,
    setValue,
    getValues,
    formState,
  } = form;

  async function parseStudentsCsv(file: File): Promise<string[][]> {
    const text = await file.text();
    return text
      .trim()
      .split("\n")
      .slice(1)
      .map((line) => line.split(",").map((v) => v.trim()));
  }

  const validateAndNormalizeData = (
    formData: NovoExameFormT,
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
      students_csv: formData.students_csv,
      vigilantes: [...(formData.vigilantes ?? [])],
      number_versions:
        formData.number_versions && formData.number_versions >= 1
          ? formData.number_versions
          : 1,
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
      setValue("number_versions", validated.number_versions);

      Object.keys(validated.number_questions).forEach((key) => {
        setValue(`number_questions.${key}`, validated.number_questions[key]);
      });

      Object.keys(validated.relative_quotations).forEach((key) => {
        setValue(
          `relative_quotations.${key}`,
          validated.relative_quotations[key],
        );
      });
    }

    setFormStep(currentStep + 1);
  };

  const handlePreviousStep = () => {
    setFormStep(formStep - 1);
  };

  const onSubmit = async (formData: NovoExameFormT) => {
    const finalData = validateAndNormalizeData(formData);

    const novoExameData: NewExamConfigI = {
      subject_id: ucID,
      topics: finalData.topics.map((topic) => topic.nome),
      fraction: finalData.fraction,
      num_variations: finalData.number_exams,
      number_versions: finalData.number_versions,
      number_questions: {},
      relative_quotations: {},
      exam_title: finalData.exam_title,
      exam_date: finalData.exam_date,
      semester: finalData.semester,
      academic_year: finalData.academic_year,
      student_tuples: finalData.students_csv
        ? await parseStudentsCsv(finalData.students_csv)
        : [],
      vigilant_keycloak_ids: finalData.vigilantes,
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
    toast.loading("A gerar exame...", { position: "top-right" });
    mutate(novoExameData, {
      onSuccess: () => {
        toast.dismiss();
        toast.success("Exame criado com sucesso!", { position: "top-right" });
        setFormStep(0);
        setValidatedData(null);
        reset();
        onClose();
      },
      onError: () => {
        toast.dismiss();
        toast.error(
          "Um erro ocorreu ao gerar exame, tente novamente mais tarde.",
          {
            position: "top-right",
          },
        );
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
        num_questions: formData.number_questions[topic.id] || 1,
        relative_weight: formData.relative_quotations[topic.id] || 1,
      })),
    };
  };

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
            {Array.from({ length: totalSteps }).map((_, index) => (
              <div key={index} className="flex items-center">
                <div
                  className={cn(
                    "w-4 h-4 rounded-full transition-all duration-300 ease-in-out",
                    index <= formStep ? "bg-primary" : "bg-primary/30",
                    index < formStep && "bg-primary",
                  )}
                />
                {index < totalSteps - 1 && (
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
          // Selecionar tópicos
          <Form {...form}>
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex flex-col flex-1 min-h-0"
            >
              <FormField
                control={control}
                name="topics"
                render={({ field }) => (
                  <FormItem className="flex flex-col flex-1 min-h-0 gap-y-4">
                    <FormLabel className="text-center block text-lg gap-1">
                      Tópicos
                    </FormLabel>
                    {topics && (
                      <CustomTable
                        isSelectable
                        data={topics
                          .filter((topic) => topic[1] > 0)
                          .map((topic) => ({
                            id: topic[0].id.toString(),
                            nome: topic[0].name,
                          }))}
                        onChange={field.onChange}
                        rowSelection={field.value ?? []}
                        rowNumber={10}
                      />
                    )}
                  </FormItem>
                )}
              />

              <div className="flex gap-3 mt-4">
                <Button
                  className="cursor-pointer"
                  variant="destructive"
                  size="sm"
                  onClick={onClose}
                >
                  Cancelar
                </Button>
                <Button
                  disabled={!(watch("topics")?.length > 0)}
                  size="sm"
                  className="cursor-pointer"
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
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex flex-col flex-1 min-h-0"
            >
              <div className="space-y-4 flex flex-col flex-1 min-h-0">
                <FormLabel className="text-center block text-lg">
                  Número de questões por tópico
                </FormLabel>

                <div className="custom-scrollbar min-h-0 overflow-y-auto flex flex-col gap-1 flex-1">
                  {watch("topics")?.map((topic) => {
                    const maxQuestions =
                      topics
                        ?.map((t) =>
                          t[0].id.toString() === topic.id ? t[1] : 0,
                        )
                        .filter((n) => n !== 0)[0] || 1;

                    return (
                      <FormItem
                        key={topic.id}
                        className="flex items-center gap-x-4"
                      >
                        <FormLabel className="shrink-0 w-fit">
                          {topic.nome} (max: {maxQuestions})
                        </FormLabel>
                        <div className="flex-1 border-b-2 border-dashed border-gray-300 mb-0.5" />
                        <FormControl className="flex-1">
                          <Input
                            className="max-w-22"
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
                              const clampedValue = Math.min(
                                Math.max(isNaN(numValue) ? 1 : numValue, 1),
                                maxQuestions,
                              );
                              setValue(
                                `number_questions.${topic.id}`,
                                clampedValue,
                              );
                            }}
                            onBlur={(e) => {
                              const value = e.target.value;

                              // Only validate and set to 1 on blur if empty
                              if (value === "") {
                                setValue(`number_questions.${topic.id}`, 1);
                                return;
                              }

                              const numValue = parseInt(value);
                              const clampedValue = Math.min(
                                Math.max(isNaN(numValue) ? 1 : numValue, 1),
                                maxQuestions,
                              );
                              setValue(
                                `number_questions.${topic.id}`,
                                clampedValue,
                              );
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
                    );
                  })}
                </div>
              </div>
              <div className="flex  gap-3 mt-4">
                <Button
                  className="cursor-pointer"
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousStep}
                >
                  Retroceder
                </Button>
                <Button
                  size="sm"
                  className="cursor-pointer"
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
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex flex-col flex-1 min-h-0"
            >
              <div className="space-y-4 flex flex-col flex-1 min-h-0">
                <div className="flex items-center gap-2 justify-center">
                  <FormLabel className="text-center block text-lg">
                    Cotações relativas por tópico
                  </FormLabel>
                  <HelperHoverCard
                    iconClassName="h-4 w-4 color-gray-500"
                    content="As cotações relativas determinam o peso de cada tópico no exame. Quanto maior a cotação de um tópico, maior será a sua importância na nota final."
                  />
                </div>

                <div className="custom-scrollbar overflow-y-auto min-h-0 flex flex-col gap-1 flex-1">
                  {watch("topics")?.map((topic) => (
                    <FormItem
                      key={topic.id}
                      className="flex items-center gap-x-4"
                    >
                      <FormLabel className="shrink-0 w-fit">
                        {topic.nome}
                      </FormLabel>
                      <div className="flex-1 border-b-2 border-dashed border-gray-300 mb-0.5" />
                      <FormControl className="flex-1">
                        <Input
                          className="max-w-22"
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
                              isNaN(numValue) || numValue < 1 ? 1 : numValue,
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
                </div>
              </div>

              <div className="flex  gap-3 mt-4">
                <Button
                  className="cursor-pointer"
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousStep}
                >
                  Retroceder
                </Button>
                <Button
                  size="sm"
                  className="cursor-pointer"
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
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex flex-col flex-1 min-h-0"
            >
              <div className="space-y-4 flex-1 min-h-0 overflow-y-auto">
                <FormLabel className="text-center block text-lg">
                  Configurações finais
                </FormLabel>

                {/* Exam title field */}
                <FormField
                  control={control}
                  name="exam_title"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <FormLabel className="shrink-0 flex items-center gap-1">
                        Título do exame
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="text"
                          placeholder="Ex: Teste Teórico 1"
                          className="w-fit"
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
                    <FormItem className="flex items-center justify-between">
                      <FormLabel className="shrink-0 flex items-center gap-1">
                        Data do exame
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <FormControl>
                        <Popover>
                          <PopoverTrigger asChild className="cursor-pointer">
                            <Button
                              type="button"
                              variant="outline"
                              id="date-picker-simple"
                              className="justify-start font-normal"
                            >
                              {field.value ? (
                                format(field.value, "dd/MM/yyyy")
                              ) : (
                                <span>Escolha uma data</span>
                              )}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                              mode="single"
                              selected={toDate(field.value)}
                              onSelect={(date) => {
                                field.onChange(
                                  date ? format(date, "yyyy-MM-dd") : "",
                                );
                              }}
                            />
                          </PopoverContent>
                        </Popover>
                      </FormControl>
                    </FormItem>
                  )}
                />

                {/* Semester field */}
                <FormField
                  control={control}
                  name="semester"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <FormLabel className="shrink-0 flex items-center gap-1">
                        Semestre
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger className="cursor-pointer">
                            <SelectValue placeholder="Selecione o semestre" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem className="cursor-pointer" value="1">
                            1º Semestre
                          </SelectItem>
                          <SelectItem className="cursor-pointer" value="2">
                            2º Semestre
                          </SelectItem>
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
                    <FormItem className="flex items-center justify-between">
                      <FormLabel className="shrink-0 flex items-center gap-1">
                        Ano letivo
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger className="cursor-pointer">
                            <SelectValue placeholder="Selecione o ano" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {yearOptions.map((year) => (
                            <SelectItem
                              className="cursor-pointer"
                              key={year}
                              value={year}
                            >
                              {year}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />

                {/* Discount field */}
                <FormField
                  control={control}
                  name="fraction"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <div className="flex items-center gap-2 justify-center">
                        <FormLabel className="shrink-0">Desconto (%)</FormLabel>
                        <HelperHoverCard
                          iconClassName="h-4 w-4 color-gray-500"
                          content={`Para cada questão errada, será descontado ${watch("fraction") || 0}% do valor da questão. Exemplo: Se uma questão vale 2 valores e o desconto é de 20%, cada erro nessa questão resulta numa penalização de 0.4 valores.`}
                        />
                      </div>
                      <FormControl>
                        <Input
                          className="w-fit"
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
              </div>

              <div className="flex gap-3">
                <Button
                  className="cursor-pointer"
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousStep}
                >
                  Retroceder
                </Button>
                <Button
                  className="cursor-pointer"
                  size="sm"
                  onClick={handleNextStep}
                  disabled={
                    !watch("exam_title") ||
                    !watch("exam_date") ||
                    !watch("academic_year") ||
                    !watch("number_exams") ||
                    !watch("semester")
                  }
                >
                  Próximo
                </Button>
              </div>
            </form>
          </Form>
        )}

        {formStep === 4 && (
          <Form {...form}>
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex flex-col flex-1 min-h-0"
            >
              <div className="space-y-6 flex-1 min-h-0 overflow-y-auto custom-scrollbar">
                <FormLabel className="text-center block text-lg">
                  Resumo do Exame
                </FormLabel>
                <div className="flex flex-col gap-1">
                  <ExamConfigCard examConfigData={getDisplayData()} />
                </div>
              </div>
              <div className="flex  gap-3 pt-4">
                <Button
                  className="cursor-pointer"
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousStep}
                >
                  Retroceder
                </Button>
                <Button
                  className="cursor-pointer"
                  size="sm"
                  onClick={handleNextStep}
                >
                  Próximo
                </Button>
              </div>
            </form>
          </Form>
        )}

        {formStep === 5 && (
          <Form {...form}>
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex flex-col flex-1 min-h-0"
            >
              <div className="space-y-6 flex-1 min-h-0 overflow-y-auto">
                <FormLabel className="text-center block text-lg">
                  Vigilantes e Alunos
                </FormLabel>
                <div className="flex flex-col gap-1">
                  <FormField
                    key="LKad71ZM"
                    control={control}
                    name="vigilantes"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center gap-1">
                          Professores Vigilantes
                          <span className="text-red-500">*</span>
                        </FormLabel>
                        <FormControl className="w-full">
                          <MultiSelect
                            emptyIndicator="Nenhum resultado encontrado"
                            value={field.value}
                            onValueChange={(e) => {
                              field.onChange(e);
                            }}
                            placeholder="Selecione varios docentes"
                            options={
                              professors
                                ?.map((p) => ({
                                  value: p.id,
                                  label:
                                    p.firstName && p.lastName
                                      ? `${p.firstName} ${p.lastName}`
                                      : p.username || p.id,
                                }))
                                .filter(
                                  (e) =>
                                    e.value !==
                                    keycloack.keycloak.tokenParsed?.sub,
                                ) || []
                            }
                            popoverClassName="w-[var(--radix-popover-trigger-width)]"
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={control}
                  name="students_csv"
                  rules={{
                    validate: (file) => {
                      if (!file) return true;
                      return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onload = (ev) => {
                          const text = ev.target?.result as string;
                          const lines = text
                            .split("\n")
                            .filter((l) => l.trim());
                          for (let i = 0; i < lines.length; i++) {
                            const cols = lines[i].split(",");
                            if (
                              cols.length < 3 ||
                              cols.some((c) => !c.trim())
                            ) {
                              resolve(
                                `Linha ${i + 1} inválida. Formato esperado: nmec, nome, email`,
                              );
                              return;
                            }
                          }
                          setValue(`number_exams`, lines.length - 1);
                          setValue(`number_versions`, lines.length - 1);
                          resolve(true);
                        };
                        reader.readAsText(file as File);
                      });
                    },
                  }}
                  render={({
                    field: { onChange, value },
                    fieldState: { error },
                  }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1">
                        Alunos (CSV)
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <p className="text-xs text-muted-foreground">
                        Formato esperado: <code>nmec, nome, email</code> (uma
                        linha por aluno)
                      </p>
                      <FormControl>
                        <div
                          className="relative border border-[#e5e5e5] rounded-lg p-8 text-center cursor-pointer"
                          onClick={() => {
                            const el = document?.getElementById(
                              "file-upload-yI1i8RdV",
                            ) as HTMLInputElement | null;
                            el?.click();
                          }}
                        >
                          <input
                            multiple
                            type="file"
                            id="file-upload-yI1i8RdV"
                            onChange={(e) =>
                              onChange(e.target.files?.[0] ?? null)
                            }
                            accept=".csv"
                            className="hidden"
                          />

                          {!value ? (
                            <div className="flex flex-col items-center space-y-3">
                              <Upload className="w-6 h-6 text-gray-400" />
                              <div className="text-sm text-gray-500">
                                Clique{" "}
                                <span className="text-[#41B5C0] font-medium">
                                  aqui
                                </span>{" "}
                                para selecionar um ficheiro
                              </div>
                            </div>
                          ) : (
                            <div className="flex flex-col gap-1">
                              <span>{value.name}</span>
                            </div>
                          )}
                        </div>
                      </FormControl>
                      {error && (
                        <p className="text-sm text-destructive">
                          {error.message}
                        </p>
                      )}
                      {value && !error && (
                        <p className="text-sm text-green-600">
                          {(value as File).name} carregado com sucesso.
                        </p>
                      )}
                    </FormItem>
                  )}
                />
                {/* Number of exams field */}
                <FormField
                  control={control}
                  name="number_exams"
                  render={() => (
                    <FormItem className="flex items-center justify-between">
                      <FormLabel className="shrink-0 flex items-center gap-1">
                        Número de exames
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          className="max-w-18.25"
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
                              isNaN(numValue) || numValue < 1 ? 1 : numValue,
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
                <FormField
                  control={control}
                  name="number_exams"
                  render={() => (
                    <FormItem className="flex items-center justify-between">
                      <FormLabel className="shrink-0 flex items-center gap-1">
                        Número de versões
                      </FormLabel>
                      <FormControl>
                        <Input
                          className="max-w-18.25"
                          type="number"
                          min="1"
                          max={watch("number_exams") || undefined}
                          placeholder="1"
                          value={watch(`number_versions`) || ""}
                          onChange={(e) => {
                            const value = e.target.value;

                            // Allow empty value for backspacing
                            if (value === "") {
                              setValue(`number_versions`, NaN);
                              return;
                            }

                            const numValue = parseInt(value);
                            setValue(
                              `number_versions`,
                              isNaN(numValue) || numValue < 1 ? 1 : numValue,
                            );
                          }}
                          onBlur={(e) => {
                            const value = e.target.value;

                            // Only validate and set to 1 on blur if empty
                            if (value === "") {
                              setValue(`number_versions`, 1);
                              return;
                            }

                            const numValue = parseInt(value);
                            if (isNaN(numValue) || numValue < 1) {
                              setValue(`number_versions`, 1);
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
              </div>

              <div className="flex  gap-3 pt-4">
                <Button
                  className="cursor-pointer"
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousStep}
                >
                  Retroceder
                </Button>
                <Button
                  size="sm"
                  className="cursor-pointer"
                  type="submit"
                  disabled={
                    isPending ||
                    !formState.isValid ||
                    !watch("students_csv") ||
                    !watch("vigilantes") ||
                    watch("vigilantes").length == 0
                  }
                >
                  {isPending ? "A gerar..." : "Gerar Exame"}
                </Button>
              </div>
            </form>
          </Form>
        )}
      </Card>
    </div>
  );
};
