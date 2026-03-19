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
import { MultiSelect } from "./multi-select";
import {
  SelectTrigger,
  SelectContent,
  Select,
  SelectGroup,
  SelectItem,
  SelectValue,
} from "./ui/select";
import { useAddUc } from "@/hooks/use-ucs";
import { useGetProfessors } from "@/hooks/use-users";

type NovaUCFormT = {
  nome: string;
  regente: string;
  professores: string[];
};

export function NovaUCForm() {
  const { mutate, isError } = useAddUc();
  const { data: professors, isLoading: loadingProfessors } = useGetProfessors();

  const form = useForm<NovaUCFormT>({
    defaultValues: {
      nome: "",
      regente: "",
      professores: [],
    },
  });

  const { handleSubmit, control, reset, watch, formState } = form;

  const onSubmit = async (formData: NovaUCFormT) => {
    mutate({
      name: formData.nome,
      regent_keycloak_id: formData.regente,
      professor_keycloak_ids: formData.professores,
    });
    if (isError) {
      toast.error("Ocurreu um erro, tente novamente mais tarde", {
        position: "top-right",
      });
    } else {
      toast.success("Unidade curricular criada com sucesso", {
        position: "top-right",
      });
    }
    reset();
  };

  return (
    <div className="w-full space-y-4">
      <Card className="border-none shadow-none">
        <CardContent>
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
                            "border-red-500",
                        )}
                        {...field}
                        placeholder="Nome da UC"
                        autoComplete="off"
                        autoFocus
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                key="5trP2rUr"
                control={control}
                name="regente"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="flex items-center gap-1">
                      <span>Regente</span>
                      <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                        disabled={loadingProfessors}
                      >
                        <SelectTrigger className="shadow-none w-full">
                          <SelectValue
                            placeholder={
                              loadingProfessors
                                ? "Loading..."
                                : "Selecione um docente"
                            }
                          />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectGroup>
                            {professors?.map((prof) => (
                              <SelectItem key={prof.id} value={prof.id}>
                                {prof.firstName && prof.lastName
                                  ? `${prof.firstName} ${prof.lastName}`
                                  : prof.username}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                    </FormControl>
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
                        options={
                          professors?.map((p) => ({
                            value: p.id,
                            label:
                              p.firstName && p.lastName
                                ? `${p.firstName} ${p.lastName}`
                                : p.username || p.id,
                          })) || []
                        }
                        popoverClassName="w-[402px]"
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              <div className="flex justify-end">
                <Button
                  disabled={
                    !watch("nome") ||
                    watch("nome").trim() === "" ||
                    !watch("regente")
                  }
                  type="submit"
                  size="sm"
                  className="font-medium"
                >
                  Criar
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
