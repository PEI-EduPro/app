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
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import "@/components/ui/table"
import "@/components/topic-check-box"
import { SubjectTable } from "@/components/topic-check-box";

type TopicSelection = {
  id: string;
  name: string;
};

type NovoExameFormT = {
  topics: TopicSelection[];
  number_questions: Record<string, number>;
  relative_quotations: Record<string, number>;
  number_exams: number;
  fraction: number;
};

export const NovoExameForm = () => {
  const [formStep, setFormStep] = useState<number>(0);
  const [validatedData, setValidatedData] = useState<NovoExameFormT | null>(null);
  const totalSteps = 5;

  const form = useForm<NovoExameFormT>({
    defaultValues: {
      topics: [],
      number_questions: {},
      relative_quotations: {},
      number_exams: 1,
      fraction: 0
    }
  });

  const { handleSubmit, control, reset, watch, setValue, getValues } = form;

  const validateAndNormalizeData = (formData: NovoExameFormT): NovoExameFormT => {
    // Create a copy of the form data
    const validated: NovoExameFormT = {
      ...formData,
      number_exams: formData.number_exams && formData.number_exams >= 1 
        ? formData.number_exams 
        : 1,
      fraction: formData.fraction !== undefined && formData.fraction >= 0 && formData.fraction <= 100 
        ? formData.fraction 
        : 0,
      number_questions: { ...formData.number_questions },
      relative_quotations: { ...formData.relative_quotations }
    };

    // Ensure all topics have valid values
    formData.topics?.forEach(topic => {
      // Validate number of questions
      const currentNumQuestions = validated.number_questions[topic.id];
      if (!currentNumQuestions || currentNumQuestions < 1 || isNaN(currentNumQuestions)) {
        validated.number_questions[topic.id] = 1;
      }

      // Validate relative quotations
      const currentRelQuotation = validated.relative_quotations[topic.id];
      if (!currentRelQuotation || currentRelQuotation < 1 || isNaN(currentRelQuotation)) {
        validated.relative_quotations[topic.id] = 1;
      }
    });

    return validated;
  };

  const handleNextStep = () => {
    const currentStep = formStep;
    const formData = getValues();
    
    // If moving to step 4 (summary page), validate and normalize data first
    if (currentStep === 3) {
      const validated = validateAndNormalizeData(formData);
      setValidatedData(validated);
      
      // Update form with validated values to ensure consistency
      setValue("number_exams", validated.number_exams);
      setValue("fraction", validated.fraction);
      
      // Update number questions
      Object.keys(validated.number_questions).forEach(key => {
        setValue(`number_questions.${key}`, validated.number_questions[key]);
      });
      
      // Update relative quotations
      Object.keys(validated.relative_quotations).forEach(key => {
        setValue(`relative_quotations.${key}`, validated.relative_quotations[key]);
      });
    }
    
    setFormStep(currentStep + 1);
  };

  const handlePreviousStep = () => {
    setFormStep(formStep - 1);
  };

  const onSubmit = async (formData: NovoExameFormT) => {
    // Use validatedData if available (from summary page), otherwise validate now
    const finalData = validatedData || validateAndNormalizeData(formData);
    
    console.log("Form submitted:", finalData);
    setFormStep(0);
    setValidatedData(null);
    reset();
    toast.success("Exame criado com sucesso!");
  };

  // Helper to get data for display - uses validated data on summary page
  const getDisplayData = () => {
    if (formStep === 4 && validatedData) {
      return validatedData;
    }
    return getValues();
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
                      <SubjectTable
                        selectedTopics={field.value}
                        onChange={field.onChange}
                      />
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

                  {watch("topics")?.map((topic) => (
                    <FormItem key={topic.id} className="flex items-center gap-x-4">
                      <FormLabel className="flex-shrink-0 w-140">{topic.name}</FormLabel>
                      <FormControl className="flex-1">
                        <Input
                          type="number"
                          min="1"
                          placeholder="1"
                          value={watch(`number_questions.${topic.id}`) || ""}
                          onChange={(e) => {
                            const value = parseInt(e.target.value);
                            setValue(`number_questions.${topic.id}`, isNaN(value) || value < 1 ? 1 : value)
                          }}
                          onBlur={(e) => {
                            const value = parseInt(e.target.value);
                            if (isNaN(value) || value < 1) {
                              setValue(`number_questions.${topic.id}`, 1);
                            }
                          }}
                          onKeyDown={(e) => {
                            if (
                              !/[0-9]/.test(e.key) &&
                              ![
                                'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
                                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                                'Home', 'End'
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
                    <FormItem key={topic.id} className="flex items-center gap-x-4">
                      <FormLabel className="flex-shrink-0 w-140">{topic.name}</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          placeholder="1"
                          value={watch(`relative_quotations.${topic.id}`) || ""}
                          onChange={(e) => {
                            const value = parseInt(e.target.value);
                            setValue(`relative_quotations.${topic.id}`, isNaN(value) || value < 1 ? 1 : value)
                          }}
                          onBlur={(e) => {
                            const value = parseInt(e.target.value);
                            if (isNaN(value) || value < 1) {
                              setValue(`relative_quotations.${topic.id}`, 1);
                            }
                          }}
                          onKeyDown={(e) => {
                            if (
                              !/[0-9]/.test(e.key) &&
                              ![
                                'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
                                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                                'Home', 'End'
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
                    <h4 className="font-semibold text-blue-800 mb-2">Como funcionam as cotações relativas?</h4>
                    <p className="text-sm text-blue-700">
                      As <span className="font-medium">cotações relativas</span> determinam o peso de cada tópico no exame.<br></br>
                      Quanto maior a cotação de um tópico, maior será a sua importância na nota final.
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
                  
                  {/* Number of exams field */}
                  <FormField
                    control={control}
                    name="number_exams"
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-x-4">
                        <FormLabel className="flex-shrink-0 w-140">
                          Número de exames
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min="1"
                            placeholder="1"
                            value={field.value || ""}
                            onChange={(e) => {
                              let value = parseInt(e.target.value);
                              
                              if (isNaN(value) || value < 1) {
                                field.onChange(1);
                              } else {
                                field.onChange(value);
                              }
                            }}
                            onBlur={(e) => {
                              const value = parseInt(e.target.value);
                              if (isNaN(value) || value < 1) {
                                field.onChange(1);
                              }
                            }}
                            onKeyDown={(e) => {
                              if (
                                !/[0-9]/.test(e.key) &&
                                ![
                                  'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
                                  'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                                  'Home', 'End'
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
                  
                  <hr/>
                  
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
                                  'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
                                  'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                                  'Home', 'End'
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
                    <h4 className="font-semibold text-amber-800 mb-2">Sobre o desconto</h4>
                    <p className="text-sm text-amber-700">
                      Para cada questão errada, será descontado <span className="font-bold">{getDisplayData().fraction || 0}%</span> do valor da questão.<br></br>
                      Exemplo: Se uma questão vale 2 valores e o desconto é de 20%, cada erro nessa questão resulta numa penalização de 0.4 valores.
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
                  
                  {/* Summary Card */}
                  <Card className="border-2 border-primary/20 bg-primary/5">
                    <CardContent className="px-6">
                      {/* Exam Count Summary */}
                      <div className="mb-6 pb-4 border-b">
                        <h3 className="text-lg font-semibold text-center mb-3">
                          Configuração Geral
                        </h3>
                        <div className="grid grid-cols-2 gap-4 text-center">
                          <div className="p-3 bg-white rounded-lg shadow-sm">
                            <p className="text-sm text-muted-foreground">Exames a gerar</p>
                            <p className="text-2xl font-bold text-primary">
                              {getDisplayData().number_exams || 1}
                            </p>
                          </div>
                          <div className="p-3 bg-white rounded-lg shadow-sm">
                            <p className="text-sm text-muted-foreground">Desconto</p>
                            <p className="text-2xl font-bold text-primary">
                              {getDisplayData().fraction || 0}%
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Topics Summary */}
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3">Tópicos Selecionados</h3>
                        <div className="space-y-2">
                          {getDisplayData().topics?.map((topic) => {
                            const numQuestions = getDisplayData().number_questions[topic.id] || 1;
                            const relativeQuotation = getDisplayData().relative_quotations[topic.id] || 1;
                            
                            return (
                              <div 
                                key={topic.id} 
                                className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
                              >
                                <div>
                                  <p className="font-medium">{topic.name}</p>
                                  <p className="text-sm text-muted-foreground">
                                    {numQuestions} pergunta{numQuestions !== 1 ? 's' : ''}
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

                      {/* Totals */}
                      <div className="pt-4 border-t">
                        <div className="flex justify-between text-center items-center">
                          <div>
                            <p className="text-sm text-muted-foreground">Total de questões</p>
                            <p className="text-xl font-bold">
                              {Object.values(getDisplayData().number_questions || {}).reduce((sum, num) => sum + (num || 1), 0)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
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
                    onClick={() => {
                      handleSubmit(onSubmit)();
                    }}
                  >
                    Gerar Exame
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