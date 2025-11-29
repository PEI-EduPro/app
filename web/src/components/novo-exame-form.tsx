import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
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
  number_of_exams: number;
};

export const NovoExameForm = () => {
  const [formStep, setFormStep] = useState<number>(0);
  const totalSteps = 3;

  const form = useForm<NovoExameFormT>({
    defaultValues: {
      topics: [],
      number_questions: {},
      relative_quotations: {},
      number_of_exams: 1
    }
  });

  const { handleSubmit, control, reset, watch, setValue } = form;

  const onSubmit = async (formData: NovoExameFormT) => {
    console.log("Form submitted:", formData);
    setFormStep(0);
    reset();
    toast.success("Form successfully submitted");
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
                      <FormLabel className="text-center block text-lg">Tópicos</FormLabel>
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
                    className="font-medium"
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
                    onClick={() => setFormStep(formStep + 1)}
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
                  <FormLabel className="text-center block text-lg">Número de questões por tópico</FormLabel>
                  {watch("topics")?.map((topic) => (
                    <FormItem key={topic.id}>
                      <FormLabel>{topic.name}</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          placeholder="1"
                          value={watch(`number_questions.${topic.id}`) || ""}
                          onChange={(e) => setValue(`number_questions.${topic.id}`, parseInt(e.target.value) || 0)}
                        />
                      </FormControl>
                    </FormItem>
                  ))}
                </div>

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="font-medium"
                    size="sm"
                    onClick={() => setFormStep(formStep - 1)}
                  >
                    Retroceder
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="font-medium"
                    onClick={() => setFormStep(formStep + 1)}
                    disabled={
                      !Object.values(watch("number_questions") || {}).every((num) => num >= 1)
                    }
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
                  <FormLabel className="text-center block text-lg">Cotações relativas por tópico</FormLabel>
                  {watch("topics")?.map((topic) => (
                    <FormItem key={topic.id}>
                      <FormLabel>{topic.name}</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          placeholder="1"
                          value={watch(`relative_quotations.${topic.id}`) || ""}
                          onChange={(e) => {
                            const value = parseInt(e.target.value);
                            setValue(`relative_quotations.${topic.id}`, isNaN(value) ? 1 : Math.max(1, value));
                          }}
                        />
                      </FormControl>
                    </FormItem>
                  ))}
                  <hr/>
                  <FormLabel className="text-center block text-base">Número de exames a gerar</FormLabel>
                  <FormField
                    control={control}
                    name="number_of_exams"
                    render={({ field }) => (
                      <FormItem>
                        <FormControl>
                          <Input
                            type="number"
                            min="1"
                            placeholder="1"
                            value={field.value || ""}
                            onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="font-medium"
                    size="sm"
                    onClick={() => setFormStep(formStep - 1)}
                  >
                    Retroceder
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    className="font-medium"
                    disabled={
                      !Object.values(watch("relative_quotations") || {}).every((num) => num >= 1) ||
                      !watch("number_of_exams") || watch("number_of_exams") < 1
                    }
                  >
                    Submeter
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