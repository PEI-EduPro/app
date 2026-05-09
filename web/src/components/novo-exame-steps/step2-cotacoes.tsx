import { Form, FormControl, FormItem, FormLabel } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import HelperHoverCard from "@/components/helper-hover-card";
import type { Step2Props } from "./types";

const NUMERIC_KEYS = ["Backspace","Delete","Tab","Escape","Enter","ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"];

export function Step2Cotacoes({ form, selectedTopics, onNext, onPrev }: Step2Props) {
  const { watch, setValue } = form;

  const setRQ = (key: string, val: number) =>
    setValue("relative_quotations", { ...form.getValues("relative_quotations"), [key]: val });

  return (
    <Form {...form}>
      <form className="flex flex-col flex-1 min-h-0">
        <div className="space-y-4 flex flex-col flex-1 min-h-0">
          <div className="flex items-center gap-2 justify-center">
            <FormLabel className="text-center block text-lg">Cotações relativas por tópico</FormLabel>
            <HelperHoverCard
              side="top"
              iconClassName="h-4 w-4 color-gray-500 cursor-pointer"
              content="As cotações relativas determinam o peso de cada tópico no exame. Quanto maior a cotação de um tópico, maior será a sua importância na nota final."
            />
          </div>
          <div className="custom-scrollbar overflow-y-auto min-h-0 flex flex-col gap-1 flex-1">
            {selectedTopics.map((topic) => (
              <FormItem key={topic.id} className="flex items-center gap-x-4">
                <FormLabel className="shrink-0 w-fit">{topic.nome}</FormLabel>
                <div className="flex-1 border-b-2 border-dashed border-gray-300 mb-0.5" />
                <FormControl className="flex-1">
                  <Input
                    className="max-w-22"
                    type="number" min="1" placeholder="1"
                    value={watch("relative_quotations")?.[Number(topic.id)] ?? ""}
                    onChange={(e) => {
                      if (e.target.value === "") { setRQ(topic.id, NaN); return; }
                      const n = parseInt(e.target.value);
                      setRQ(topic.id, isNaN(n) || n < 1 ? 1 : n);
                    }}
                    onBlur={(e) => {
                      if (e.target.value === "") { setRQ(topic.id, 1); return; }
                      const n = parseInt(e.target.value);
                      if (isNaN(n) || n < 1) setRQ(topic.id, 1);
                    }}
                    onKeyDown={(e) => { if (!/[0-9]/.test(e.key) && !NUMERIC_KEYS.includes(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault(); }}
                  />
                </FormControl>
              </FormItem>
            ))}
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
