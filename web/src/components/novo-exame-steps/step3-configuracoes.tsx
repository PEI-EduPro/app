import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import HelperHoverCard from "@/components/helper-hover-card";
import { format, toDate } from "date-fns";
import type { StepProps } from "./types";

const NUMERIC_KEYS = ["Backspace","Delete","Tab","Escape","Enter","ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"];

const currentYear = new Date().getFullYear();
const yearOptions = [
  `${currentYear - 1}/${String(currentYear).slice(-2)}`,
  `${currentYear}/${String(currentYear + 1).slice(-2)}`,
];

export function Step3Configuracoes({ form, onNext, onPrev }: StepProps) {
  const { handleSubmit, control, watch } = form;

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit(() => {})} className="flex flex-col flex-1 min-h-0">
        <div className="space-y-4 flex-1 min-h-0 overflow-y-auto">
          <FormLabel className="text-center block text-lg">Configurações finais</FormLabel>

          <FormField control={control} name="exam_title" render={({ field }) => (
            <FormItem className="flex items-center justify-between">
              <FormLabel className="shrink-0 flex items-center gap-1">Título do exame <span className="text-red-500">*</span></FormLabel>
              <FormControl><Input type="text" placeholder="Ex: Teste Teórico 1" className="w-fit" {...field} /></FormControl>
            </FormItem>
          )} />

          <FormField control={control} name="exam_date" render={({ field }) => (
            <FormItem className="flex items-center justify-between">
              <FormLabel className="shrink-0 flex items-center gap-1">Data do exame <span className="text-red-500">*</span></FormLabel>
              <FormControl>
                <Popover>
                  <PopoverTrigger asChild className="cursor-pointer">
                    <Button type="button" variant="outline" className="justify-start font-normal">
                      {field.value ? format(field.value, "dd/MM/yyyy") : <span>Escolha uma data</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      disabled={(date) => date < new Date()}
                      selected={toDate(field.value)}
                      onSelect={(date) => field.onChange(date ? format(date, "yyyy-MM-dd") : "")}
                    />
                  </PopoverContent>
                </Popover>
              </FormControl>
            </FormItem>
          )} />

          <FormField control={control} name="semester" render={({ field }) => (
            <FormItem className="flex items-center justify-between">
              <FormLabel className="shrink-0 flex items-center gap-1">Semestre <span className="text-red-500">*</span></FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger className="cursor-pointer"><SelectValue placeholder="Selecione o semestre" /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem className="cursor-pointer" value="1">1º Semestre</SelectItem>
                  <SelectItem className="cursor-pointer" value="2">2º Semestre</SelectItem>
                </SelectContent>
              </Select>
            </FormItem>
          )} />

          <FormField control={control} name="academic_year" render={({ field }) => (
            <FormItem className="flex items-center justify-between">
              <FormLabel className="shrink-0 flex items-center gap-1">Ano letivo <span className="text-red-500">*</span></FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger className="cursor-pointer"><SelectValue placeholder="Selecione o ano" /></SelectTrigger></FormControl>
                <SelectContent>
                  {yearOptions.map((year) => (
                    <SelectItem className="cursor-pointer" key={year} value={year}>{year}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormItem>
          )} />

          <FormField control={control} name="fraction" render={({ field }) => (
            <FormItem className="flex items-center justify-between">
              <div className="flex items-center gap-2 justify-center">
                <FormLabel className="shrink-0">Desconto (%)</FormLabel>
                <HelperHoverCard
                  side="bottom"
                  iconClassName="h-4 w-4 color-gray-500 cursor-pointer"
                  content={`Para cada questão errada, será descontado ${watch("fraction") || 0}% do valor da questão. Exemplo: Se uma questão vale 2 valores e o desconto é de 20%, cada erro nessa questão resulta numa penalização de 0.4 valores.`}
                />
              </div>
              <FormControl>
                <Input
                  className="w-fit" type="number" min="0" max="100" placeholder="0"
                  value={field.value || ""}
                  onChange={(e) => {
                    const v = parseInt(e.target.value);
                    field.onChange(isNaN(v) ? 0 : Math.max(0, Math.min(100, v)));
                  }}
                  onBlur={(e) => { if (isNaN(parseInt(e.target.value))) field.onChange(0); }}
                  onKeyDown={(e) => { if (!/[0-9]/.test(e.key) && !NUMERIC_KEYS.includes(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault(); }}
                />
              </FormControl>
            </FormItem>
          )} />
        </div>

        <div className="flex gap-3">
          <Button className="cursor-pointer" variant="outline" size="sm" onClick={onPrev}>Retroceder</Button>
          <Button
            className="cursor-pointer" size="sm" onClick={onNext}
            disabled={!watch("exam_title") || !watch("exam_date") || !watch("academic_year") || !watch("semester")}
          >
            Próximo
          </Button>
        </div>
      </form>
    </Form>
  );
}
