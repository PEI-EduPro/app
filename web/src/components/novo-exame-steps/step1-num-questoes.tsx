import { Form, FormControl, FormItem, FormLabel } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Step1Props } from "./types";

const NUMERIC_KEYS = ["Backspace","Delete","Tab","Escape","Enter","ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"];

export function Step1NumQuestoes({ form, topics, selectedTopics, onNext, onPrev }: Step1Props) {
  const { watch, setValue } = form;

  const setNQ = (key: string, val: number) =>
    setValue("number_questions", { ...form.getValues("number_questions"), [key]: val });

  return (
    <Form {...form}>
      <form className="flex flex-col flex-1 min-h-0">
        <div className="space-y-4 flex flex-col flex-1 min-h-0">
          <FormLabel className="text-center block text-lg">Número de questões por tópico</FormLabel>
          <div className="custom-scrollbar min-h-0 overflow-y-auto flex flex-col gap-1 flex-1">
            {selectedTopics.map((topic) => {
              const maxQuestions = topics?.map((t) => t[0].id.toString() === topic.id ? t[1] : 0).filter((n) => n !== 0)[0] || 1;
              return (
                <FormItem key={topic.id} className="flex items-center gap-x-4">
                  <FormLabel className="shrink-0 w-fit">{topic.nome} (max: {maxQuestions})</FormLabel>
                  <div className="flex-1 border-b-2 border-dashed border-gray-300 mb-0.5" />
                  <FormControl className="flex-1">
                    <Input
                      className="max-w-22"
                      type="number" min="1" max={maxQuestions} placeholder="1"
                      value={watch("number_questions")?.[Number(topic.id)] ?? ""}
                      onChange={(e) => {
                        if (e.target.value === "") { setNQ(topic.id, NaN); return; }
                        const n = parseInt(e.target.value);
                        setNQ(topic.id, Math.min(Math.max(isNaN(n) ? 1 : n, 1), maxQuestions));
                      }}
                      onBlur={(e) => {
                        if (e.target.value === "") { setNQ(topic.id, 1); return; }
                        const n = parseInt(e.target.value);
                        setNQ(topic.id, Math.min(Math.max(isNaN(n) ? 1 : n, 1), maxQuestions));
                      }}
                      onKeyDown={(e) => { if (!/[0-9]/.test(e.key) && !NUMERIC_KEYS.includes(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault(); }}
                    />
                  </FormControl>
                </FormItem>
              );
            })}
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <Button className="cursor-pointer" variant="outline" size="sm" onClick={onPrev}>Retroceder</Button>
          <Button size="sm" className="cursor-pointer" onClick={onNext}>Próximo</Button>
        </div>
      </form>
    </Form>
  );
}
