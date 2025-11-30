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
import { Upload } from "lucide-react";
import { MultiSelect } from "./multi-select";
import {
  SelectTrigger,
  SelectContent,
  Select,
  SelectGroup,
  SelectItem,
  SelectValue,
} from "./ui/select";

type NovaUCFormT = {
  nome: string;
  imagem: File | null;
  regente: string;
  professores: string[];
  alunos: string[];
  docs: FileList | null;
};

export function NovaUCForm() {
  const [formStep, setFormStep] = useState<number>(0);
  const totalSteps = 3;

  const form = useForm<NovaUCFormT>({
    defaultValues: {
      nome: "",
      imagem: null,
      regente: "",
      professores: [],
      alunos: [],
      docs: null,
    },
  });

  const { handleSubmit, control, reset, watch, formState } = form;

  const onSubmit = async (formData: unknown) => {
    console.log(formData);
    setFormStep(0);
    reset();
    toast.success("Form successfully submitted");
  };

  const options = [
    { value: "p1", label: "Joao Rafael" },
    { value: "p2", label: "Maria Silva" },
    { value: "p3", label: "Pedro Santos" },
  ];

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
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <FormField
                  key="rmupBCNm"
                  control={control}
                  name="nome"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1">
                        <span>Nome</span>
                        <span className="text-red-500">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          className={cn(
                            "shadow-none",
                            formState.touchedFields.nome &&
                              (!field.value || field.value.trim() == "") &&
                              "border-red-500"
                          )}
                          {...field}
                          placeholder="Nome da UC"
                          autoComplete="off"
                        />
                      </FormControl>
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />

                <FormField
                  key="yI1i8RdV"
                  control={control}
                  name="imagem"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Imagem</FormLabel>
                      <FormControl>
                        <div
                          className="relative border-[1px] border-[#e5e5e5] rounded-lg p-8 text-center cursor-pointer"
                          onClick={() => {
                            const el = document?.getElementById(
                              "file-upload-yI1i8RdV"
                            ) as HTMLInputElement | null;
                            el?.click();
                          }}
                        >
                          <input
                            type="file"
                            id="file-upload-yI1i8RdV"
                            onChange={(e) => {
                              field.onChange(e.target.files?.[0] || null);
                            }}
                            accept="image/*, application/pdf"
                            className="hidden"
                          />

                          {!field.value ? (
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
                            <span>{field.value.name}</span>
                          )}
                        </div>
                      </FormControl>
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="font-medium"
                    size="sm"
                    disabled
                    variant="outline"
                  >
                    Retroceder
                  </Button>
                  <Button
                    disabled={!watch("nome") || watch("nome").trim() === ""}
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
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <FormField
                  key="5trP2rUr"
                  control={control}
                  name="regente"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Regente</FormLabel>
                      <FormControl>
                        <Select
                          value={field.value}
                          onValueChange={field.onChange}
                        >
                          <SelectTrigger className="shadow-none w-full">
                            <SelectValue placeholder="Selecione um docente" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              {options.map((option, index) => (
                                <SelectItem
                                  key={`option.value${index}`}
                                  value={option.value}
                                >
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </FormControl>
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />

                <FormField
                  key="LKad71ZM"
                  control={control}
                  name="professores"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Professores</FormLabel>
                      <FormControl>
                        <MultiSelect
                          value={field.value}
                          onValueChange={(e) => field.onChange(e)}
                          placeholder="Selecione varios docentes"
                          options={options}
                          popoverClassName="w-[402px]"
                        />
                      </FormControl>
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="font-medium"
                    size="sm"
                    variant="outline"
                    onClick={() => setFormStep(formStep - 1)}
                  >
                    Retroceder
                  </Button>
                  <Button
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

          {formStep === 2 && (
            <Form {...form}>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-y-4">
                <FormField
                  key="XwheAcSD"
                  control={control}
                  name="alunos"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Alunos</FormLabel>
                      <FormControl>
                        <MultiSelect
                          value={field.value}
                          onValueChange={(e) => field.onChange(e)}
                          placeholder="Selecione varios alunos"
                          options={options}
                          popoverClassName="w-[402px]"
                        />
                      </FormControl>
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />

                <FormField
                  key="yI1i8RdV"
                  control={control}
                  name="docs"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Documentos</FormLabel>
                      <FormControl>
                        <div
                          className="relative border-[1px] border-[#e5e5e5] rounded-lg p-8 text-center cursor-pointer"
                          onClick={() => {
                            const el = document?.getElementById(
                              "file-upload-yI1i8RdV"
                            ) as HTMLInputElement | null;
                            el?.click();
                          }}
                        >
                          <input
                            multiple
                            type="file"
                            id="file-upload-yI1i8RdV"
                            onChange={(e) => {
                              field.onChange(e.target.files);
                            }}
                            accept="image/*, application/pdf"
                            className="hidden"
                          />

                          {!field.value || field.value.length === 0 ? (
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
                              {Array.from(field.value).map((file, index) => (
                                <span key={index}>{file.name}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </FormControl>
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />

                <div className="flex justify-between">
                  <Button
                    type="button"
                    className="font-medium"
                    size="sm"
                    variant="outline"
                    onClick={() => setFormStep(formStep - 1)}
                  >
                    Retroceder
                  </Button>
                  <Button type="submit" size="sm" className="font-medium">
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
}
