import { useState } from "react";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import HelperHoverCard from "@/components/helper-hover-card";
import type { Step2Props } from "./types";

const NUMERIC_KEYS = [
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
];

export function Step2Cotacoes({
  form,
  selectedTopics,
  onNext,
  onPrev,
}: Step2Props) {
  const { watch, setValue, control } = form;
  const [usePercent, setUsePercent] = useState(false);
  const [percentValues, setPercentValues] = useState<Record<string, number>>({});

  const relativeQuotations = watch("relative_quotations");
  const numberQuestions = watch("number_questions");
  const fraction = watch("fraction") ?? 0;

  const totalWeight = selectedTopics.reduce(
    (s, t) => s + (relativeQuotations?.[Number(t.id)] || 0),
    0,
  );

  function setRQ(key: string, val: number) {
    setValue("relative_quotations", {
      ...form.getValues("relative_quotations"),
      [key]: val,
    });
  }

  // Convert a percentage to a weight that preserves ratios with other topics
  function percentToWeight(_id: string, pct: number): number {
    return pct / 10;
  }

  function handlePercentChange(id: string, pct: number) {
    const clamped = Math.max(0, Math.min(99.9, pct));
    setPercentValues((p) => ({ ...p, [id]: clamped }));
    setRQ(id, percentToWeight(id, clamped));
  }

  function perQuestionValue(topicId: string): string {
    if (!totalWeight) return "—";
    const w = relativeQuotations?.[Number(topicId)] || 0;
    const nq = numberQuestions?.[Number(topicId)] || 1;
    const val = ((w / totalWeight) * 20) / nq;
    return val % 1 === 0 ? val.toString() : val.toFixed(3).replace(/0+$/, "");
  }

  function switchToPercent() {
    const initial = Object.fromEntries(
      selectedTopics.map((t) => {
        const w = form.getValues("relative_quotations")?.[Number(t.id)] || 0;
        return [t.id, +(w * 10).toFixed(1)];
      }),
    );
    setPercentValues(initial);
    setUsePercent(true);
  }

  function switchToWeights() {
    setPercentValues({});
    setUsePercent(false);
  }

  return (
    <Form {...form}>
      <form className="flex flex-col flex-1 min-h-0">
        <div className="space-y-4 flex flex-col flex-1 min-h-0">
          <div className="flex items-center gap-2 justify-center">
            <FormLabel className="text-center block text-lg">
              Cotações por tópico
            </FormLabel>
            <HelperHoverCard
              side="top"
              iconClassName="h-4 w-4 color-gray-500 cursor-pointer"
              content="As cotações relativas determinam o peso de cada tópico no exame. O total equivale a 20 valores."
            />
          </div>

          <div className="flex items-center gap-2 justify-end text-sm">
            <span className="text-muted-foreground">Modo:</span>
            <button
              type="button"
              onClick={switchToWeights}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors cursor-pointer ${!usePercent ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}
            >
              Pesos relativos
            </button>
            <button
              type="button"
              onClick={switchToPercent}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors cursor-pointer ${usePercent ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}
            >
              Percentagem
            </button>
          </div>

          <div className="custom-scrollbar overflow-y-auto min-h-0 flex flex-col gap-1 flex-1">
            {selectedTopics.map((topic) => (
              <FormItem key={topic.id} className="flex items-center gap-x-4">
                <FormLabel className="shrink-0 w-fit">{topic.nome}</FormLabel>
                <div className="flex-1 border-b-2 border-dashed border-gray-300 mb-0.5" />
                <span className="text-xs text-muted-foreground shrink-0 w-24 text-right">
                  {perQuestionValue(topic.id)} val/q
                </span>
                <div className="flex items-center gap-1 w-28 justify-end">
                  {usePercent ? (
                    <>
                      <Input
                        className="max-w-22"
                        type="number"
                        min="0"
                        max="99.9"
                        step="0.1"
                        placeholder="0"
                        value={percentValues[topic.id] ?? ""}
                        onChange={(e) => {
                          const v = parseFloat(e.target.value);
                          handlePercentChange(topic.id, isNaN(v) ? 0 : v);
                        }}
                        onKeyDown={(e) => {
                          if (
                            !/[0-9.]/.test(e.key) &&
                            !NUMERIC_KEYS.includes(e.key) &&
                            !e.ctrlKey &&
                            !e.metaKey
                          )
                            e.preventDefault();
                        }}
                      />
                      <span className="text-sm text-muted-foreground shrink-0">
                        %
                      </span>
                    </>
                  ) : (
                    <Input
                      className="max-w-22"
                      type="number"
                      min="1"
                      placeholder="1"
                      value={relativeQuotations?.[Number(topic.id)] ?? ""}
                      onChange={(e) => {
                        if (e.target.value === "") {
                          setRQ(topic.id, NaN);
                          return;
                        }
                        const n = parseInt(e.target.value);
                        setRQ(topic.id, isNaN(n) || n < 1 ? 1 : n);
                      }}
                      onBlur={(e) => {
                        if (e.target.value === "") {
                          setRQ(topic.id, 1);
                          return;
                        }
                        const n = parseInt(e.target.value);
                        if (isNaN(n) || n < 1) setRQ(topic.id, 1);
                      }}
                      onKeyDown={(e) => {
                        if (
                          !/[0-9]/.test(e.key) &&
                          !NUMERIC_KEYS.includes(e.key) &&
                          !e.ctrlKey &&
                          !e.metaKey
                        )
                          e.preventDefault();
                      }}
                    />
                  )}
                </div>
              </FormItem>
            ))}
          </div>

          <div className="flex items-center pt-2 border-t">
            <FormField
              control={control}
              name="fraction"
              render={({ field }) => (
                <FormItem className="flex items-center gap-2 m-0">
                  <div className="flex items-center gap-1">
                    <FormLabel className="shrink-0 text-sm">
                      Desconto (%)
                    </FormLabel>
                    <HelperHoverCard
                      side="top"
                      iconClassName="h-4 w-4 color-gray-500 cursor-pointer"
                      content={`Para cada questão errada, será descontado ${fraction}% do valor da questão.`}
                    />
                  </div>
                  <FormControl>
                    <Input
                      className="w-20"
                      type="number"
                      min="0"
                      max="100"
                      placeholder="0"
                      value={field.value || ""}
                      onChange={(e) => {
                        const v = parseInt(e.target.value);
                        field.onChange(
                          isNaN(v) ? 0 : Math.max(0, Math.min(100, v)),
                        );
                      }}
                      onBlur={(e) => {
                        if (isNaN(parseInt(e.target.value))) field.onChange(0);
                      }}
                      onKeyDown={(e) => {
                        if (
                          !/[0-9]/.test(e.key) &&
                          !NUMERIC_KEYS.includes(e.key) &&
                          !e.ctrlKey &&
                          !e.metaKey
                        )
                          e.preventDefault();
                      }}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </div>
        </div>

        <div className="flex gap-3 mt-4">
          <Button
            className="cursor-pointer"
            variant="outline"
            size="sm"
            onClick={onPrev}
          >
            Retroceder
          </Button>
          <Button size="sm" className="cursor-pointer" onClick={onNext}>
            Próximo
          </Button>
        </div>
      </form>
    </Form>
  );
}
