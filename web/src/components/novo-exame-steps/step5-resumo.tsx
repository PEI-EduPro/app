import { Form } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { FormLabel } from "@/components/ui/form";
import { ExamConfigCard } from "@/components/exam-config-card";
import type { Step5Props } from "./types";

export function Step5Resumo({ form, topics, onPrev, isPending, onSubmit }: Step5Props) {
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col flex-1 min-h-0">
        <div className="space-y-6 flex-1 min-h-0 overflow-y-auto custom-scrollbar">
          <FormLabel className="text-center block text-lg">Resumo do Exame</FormLabel>
          <ExamConfigCard examConfigData={form.getValues()} allTopics={topics} />
        </div>
        <div className="flex gap-3 pt-4">
          <Button className="cursor-pointer" variant="outline" size="sm" onClick={onPrev}>Retroceder</Button>
          <Button size="sm" className="cursor-pointer" type="submit">
            {isPending ? "A gerar..." : "Gerar Exame"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
