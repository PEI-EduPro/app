import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MultiSelect } from "@/components/multi-select";
import HelperHoverCard from "@/components/helper-hover-card";
import { Separator } from "@/components/ui/separator";
import { FileText, TriangleAlert, Upload } from "lucide-react";
import { useGetProfessors } from "@/hooks/use-users";
import { useKeycloak } from "@/hooks/use-keycloak";
import type { Step4Props } from "./types";

const NUMERIC_KEYS = ["Backspace","Delete","Tab","Escape","Enter","ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"];

export function Step4VigilantesAlunos({ form, studentsCsv, setStudentsCsv, onNext, onPrev, isPending }: Step4Props) {
  const { control, watch, setValue, formState } = form;
  const { data: professors } = useGetProfessors();
  const { keycloak } = useKeycloak();

  return (
    <Form {...form}>
      <form className="flex flex-col flex-1 min-h-0">
        <div className="space-y-6 flex-1 min-h-0 overflow-y-auto">
          <FormLabel className="text-center block text-lg">Vigilantes e Alunos</FormLabel>

          <FormField control={control} name="vigilant_keycloak_ids" render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center gap-1">Professores Vigilantes <span className="text-red-500">*</span></FormLabel>
              <FormControl className="w-full">
                <MultiSelect
                  emptyIndicator="Nenhum resultado encontrado"
                  value={field.value}
                  onValueChange={field.onChange}
                  placeholder="Selecione varios docentes"
                  options={
                    professors
                      ?.map((p) => ({
                        value: p.id,
                        label: p.firstName && p.lastName ? `${p.firstName} ${p.lastName}` : p.username || p.id,
                      }))
                      .filter((e) => e.value !== keycloak.tokenParsed?.sub) || []
                  }
                  popoverClassName="w-[var(--radix-popover-trigger-width)]"
                />
              </FormControl>
            </FormItem>
          )} />

          <FormField
            control={control}
            name="student_tuples"
            rules={{
              validate: () => {
                if (!studentsCsv) return true;
                return new Promise((resolve) => {
                  const reader = new FileReader();
                  reader.onload = (ev) => {
                    const text = ev.target?.result as string;
                    const lines = text.split("\n").filter((l) => l.trim());
                    for (let i = 0; i < lines.length; i++) {
                      const cols = lines[i].split(",");
                      if (cols.length < 3 || cols.some((c) => !c.trim())) {
                        resolve(`Linha ${i + 1} inválida. Formato esperado: nmec, nome, email`);
                        return;
                      }
                    }
                    setValue("student_tuples", lines.slice(1).map((line) => line.split(",").map((c) => c.trim())));
                    resolve(true);
                  };
                  reader.readAsText(studentsCsv as File);
                });
              },
            }}
            render={({ field: { onChange }, fieldState: { error } }) => (
              <FormItem>
                <FormLabel className="flex items-center gap-1">
                  Alunos (CSV) <span className="text-red-500">*</span>
                  <HelperHoverCard
                    side="bottom"
                    iconClassName="h-4 w-4 color-gray-500 cursor-pointer"
                    content={
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded bg-gray-700 flex items-center justify-center shrink-0">
                            <FileText className="w-3.5 h-3.5 text-white" />
                          </div>
                          <div>
                            <p className="font-semibold text-sm leading-tight text-gray-800">Formato CSV</p>
                            <p className="text-xs text-gray-400 font-mono">.csv · separado por vírgulas</p>
                          </div>
                        </div>
                        <Separator className="bg-gray-300" />
                        <div className="space-y-1.5">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Colunas obrigatórias</p>
                          {[
                            { col: "nmec", desc: "Número de aluno único", example: "112903" },
                            { col: "nome", desc: "Primeiro nome", example: "Marta" },
                            { col: "email", desc: "Email institucional", example: undefined },
                          ].map(({ col, desc, example }) => (
                            <div key={col} className="flex items-start gap-2">
                              <code className="text-xs bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded w-14 text-center shrink-0">{col}</code>
                              <span className="text-xs text-gray-600 leading-snug">{desc} {example && <span className="text-gray-400">(ex: {example})</span>}</span>
                            </div>
                          ))}
                        </div>
                        <div className="bg-gray-800 rounded-md px-3 py-2">
                          <p className="text-[10px] text-gray-500 mb-1 uppercase tracking-wide">Exemplo</p>
                          <pre className="text-[11px] text-gray-300 font-mono leading-relaxed">{`nmec, nome, email\n112903, Marta, marta@ua.pt\n112904, Maria, maria@ua.pt`}</pre>
                        </div>
                        <div className="flex gap-1.5 items-start rounded-md bg-amber-50 border border-amber-200 px-2.5 py-2">
                          <TriangleAlert className="w-3 h-3 text-amber-600 mt-0.5 shrink-0" />
                          <p className="text-xs text-amber-700 leading-snug">
                            A linha de cabeçalho é obrigatória. Sem <code className="font-mono text-[10px]">nmec</code> duplicados ou linhas vazias.
                          </p>
                        </div>
                      </div>
                    }
                  />
                </FormLabel>
                <p className="text-xs text-muted-foreground">Formato esperado: <code>nmec, nome, email</code> (uma linha por aluno)</p>
                <FormControl>
                  <div
                    className="relative border border-[#e5e5e5] rounded-lg p-8 text-center cursor-pointer"
                    onClick={() => (document.getElementById("file-upload-yI1i8RdV") as HTMLInputElement | null)?.click()}
                  >
                    <input
                      multiple type="file" id="file-upload-yI1i8RdV" accept=".csv" className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0] ?? null;
                        onChange(file);
                        setStudentsCsv(file);
                        if (file) {
                          const reader = new FileReader();
                          reader.onload = (ev) => {
                            const lines = (ev.target?.result as string).split("\n").filter((l) => l.trim());
                            if (lines.length > 1) {
                              setValue("num_variations", lines.length - 1);
                              setValue("num_versions", lines.length - 1);
                            }
                          };
                          reader.readAsText(file);
                        }
                      }}
                    />
                    {!studentsCsv ? (
                      <div className="flex flex-col items-center space-y-3">
                        <Upload className="w-6 h-6 text-gray-400" />
                        <div className="text-sm text-gray-500">Clique <span className="text-[#41B5C0] font-medium">aqui</span> para selecionar um ficheiro</div>
                      </div>
                    ) : (
                      <span>{studentsCsv.name}</span>
                    )}
                  </div>
                </FormControl>
                {error && <p className="text-sm text-destructive">{error.message}</p>}
                {studentsCsv && !error && <p className="text-sm text-green-600">{studentsCsv.name} carregado com sucesso.</p>}
              </FormItem>
            )}
          />

          <FormField control={control} name="num_variations" render={() => (
            <FormItem className="flex items-center justify-between">
              <FormLabel className="shrink-0 flex items-center gap-1">Número de exames <span className="text-red-500">*</span></FormLabel>
              <FormControl>
                <Input
                  className="max-w-18.25" type="number" min="1" placeholder="1"
                  value={watch("num_variations") || ""}
                  onChange={(e) => {
                    if (e.target.value === "") { setValue("num_variations", NaN); return; }
                    const n = parseInt(e.target.value);
                    setValue("num_variations", isNaN(n) || n < 1 ? 1 : n);
                  }}
                  onBlur={(e) => {
                    if (e.target.value === "") { setValue("num_variations", 1); return; }
                    const n = parseInt(e.target.value);
                    if (isNaN(n) || n < 1) setValue("num_variations", 1);
                  }}
                  onKeyDown={(e) => { if (!/[0-9]/.test(e.key) && !NUMERIC_KEYS.includes(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault(); }}
                />
              </FormControl>
            </FormItem>
          )} />

          <FormField control={control} name="num_versions" render={() => (
            <FormItem className="flex items-center justify-between">
              <FormLabel className="flex items-center gap-1">
                Número de versões
                <HelperHoverCard
                  side="bottom"
                  iconClassName="h-4 w-4 color-gray-500 cursor-pointer"
                  content={
                    <p className="text-xs text-gray-600 leading-relaxed">
                      Cada versão tem <span className="font-medium text-gray-800">questões diferentes</span> dos mesmos tópicos.
                      Quando uma questão se repete, a <span className="font-medium text-gray-800">ordem das opções e das questões</span> é baralhada.
                      Com <span className="font-medium text-gray-800">100 exames e 10 versões</span>, cada versão é repetida <span className="font-medium text-gray-800">10 vezes</span>, ou seja, 10 alunos terão exatamente o mesmo exame.
                    </p>
                  }
                />
              </FormLabel>
              <FormControl>
                <Input
                  className="max-w-18.25" type="number" min="1" max={watch("num_variations") || undefined} placeholder="1"
                  value={watch("num_versions") || ""}
                  onChange={(e) => {
                    if (e.target.value === "") { setValue("num_versions", NaN); return; }
                    const n = parseInt(e.target.value);
                    setValue("num_versions", isNaN(n) || n < 1 ? 1 : n);
                  }}
                  onBlur={(e) => {
                    if (e.target.value === "") { setValue("num_versions", 1); return; }
                    const n = parseInt(e.target.value);
                    if (isNaN(n) || n < 1) setValue("num_versions", 1);
                  }}
                  onKeyDown={(e) => { if (!/[0-9]/.test(e.key) && !NUMERIC_KEYS.includes(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault(); }}
                />
              </FormControl>
            </FormItem>
          )} />
        </div>

        <div className="flex gap-3 pt-4">
          <Button className="cursor-pointer" variant="outline" size="sm" onClick={onPrev}>Retroceder</Button>
          <Button
            className="cursor-pointer" size="sm" onClick={onNext}
            disabled={
              isPending || !formState.isValid ||
              !watch("student_tuples") ||
              !watch("vigilant_keycloak_ids") ||
              watch("vigilant_keycloak_ids")?.length === 0 ||
              watch("num_variations") < 1
            }
          >
            Próximo
          </Button>
        </div>
      </form>
    </Form>
  );
}
