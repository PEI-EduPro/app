import { Form, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { CustomTable } from "@/components/custom-table";
import type { Step0Props } from "./types";

export function Step0Topicos({ form, topics, selectedTopics, setSelectedTopics, onNext, onClose }: Step0Props) {
  const { handleSubmit, control, setValue, watch } = form;

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit(() => {})} className="flex flex-col flex-1 min-h-0">
        <FormField
          control={control}
          name="topics"
          render={() => (
            <FormItem className="flex flex-col flex-1 min-h-0 gap-y-4">
              <FormLabel className="text-center block text-lg gap-1">Tópicos</FormLabel>
              {topics && (
                <CustomTable
                  isSelectable
                  data={topics
                    .filter((topic) => topic[1] > 0)
                    .map((topic) => ({ id: topic[0].id.toString(), nome: topic[0].name }))}
                  onChange={(val) => {
                    setSelectedTopics(val.map((v) => ({ id: v.id, nome: v.nome })));
                    setValue("topics", val.map((v) => v.id));
                    const currentNQ = form.getValues("number_questions") || {};
                    const currentRQ = form.getValues("relative_quotations") || {};
                    const selectedIds = new Set(val.map((v) => v.id));
                    setValue("number_questions", Object.fromEntries(Object.entries(currentNQ).filter(([k]) => selectedIds.has(k))));
                    setValue("relative_quotations", Object.fromEntries(Object.entries(currentRQ).filter(([k]) => selectedIds.has(k))));
                    val.forEach((v) => {
                      if (currentNQ[Number(v.id)] === undefined)
                        setValue("number_questions", { ...form.getValues("number_questions"), [v.id]: 1 });
                      if (currentRQ[Number(v.id)] === undefined)
                        setValue("relative_quotations", { ...form.getValues("relative_quotations"), [v.id]: 1 });
                    });
                  }}
                  rowSelection={selectedTopics}
                  rowNumber={10}
                />
              )}
            </FormItem>
          )}
        />
        <div className="flex gap-3 mt-4">
          <Button className="cursor-pointer" variant="destructive" size="sm" onClick={onClose}>Cancelar</Button>
          <Button disabled={!(watch("topics")?.length > 0)} size="sm" className="cursor-pointer" onClick={onNext}>Próximo</Button>
        </div>
      </form>
    </Form>
  );
}
