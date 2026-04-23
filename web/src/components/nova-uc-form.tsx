import { useForm, Controller } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAddUc, useUpdateUc, useGetUcProfessors, useGetUcRegent } from "@/hooks/use-ucs";
import { useGetProfessors } from "@/hooks/use-users";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";
import { useState } from "react";

type UCFormT = {
  nome: string;
  regente: string;
  professores: string[];
};

function formatName(p: { firstName?: string; lastName?: string; first_name?: string; last_name?: string; username?: string; email?: string }) {
  return (p.firstName && p.lastName)
    ? `${p.firstName} ${p.lastName}`
    : (p.first_name && p.last_name)
      ? `${p.first_name} ${p.last_name}`
      : p.username || p.email || "";
}

interface UCFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
  ucId?: number;
  initialRegente?: string;
  initialProfessores?: string[];
  lockRegente?: boolean;
}

function UCFormInner({ onSuccess, onCancel, ucId, initialRegente = "", initialProfessores = [], lockRegente = false }: UCFormProps) {
  const isEdit = !!ucId;
  const { mutate: addUc } = useAddUc(onSuccess);
  const { mutate: updateUc } = useUpdateUc(ucId ?? 0);
  const { data: professors = [], isLoading: loadingProfessors } = useGetProfessors();
  const [regenteSearch, setRegenteSearch] = useState("");
  const [professoresSearch, setProfessoresSearch] = useState("");

  const { handleSubmit, control, reset, watch, formState } = useForm<UCFormT>({
    defaultValues: { nome: "", regente: initialRegente, professores: initialProfessores },
  });

  const selectedRegente = watch("regente");

  const filteredRegente = professors.filter((p) => {
    const q = regenteSearch.toLowerCase();
    return formatName(p).toLowerCase().includes(q) || (p.email || "").toLowerCase().includes(q);
  });

  const filteredProfessores = professors
    .filter((p) => p.id !== selectedRegente)
    .filter((p) => {
      const q = professoresSearch.toLowerCase();
      return formatName(p).toLowerCase().includes(q) || (p.email || "").toLowerCase().includes(q);
    });

  const onSubmit = (formData: UCFormT) => {
    if (isEdit) {
      updateUc({ regent_keycloak_id: formData.regente, professor_keycloak_ids: formData.professores });
      onSuccess?.();
    } else {
      addUc({ name: formData.nome, regent_keycloak_id: formData.regente, professor_keycloak_ids: formData.professores });
      reset();
    }
  };

  function SearchableList({
    items,
    search,
    onSearch,
    selected,
    onToggle,
    multi = false,
  }: {
    items: typeof professors;
    search: string;
    onSearch: (v: string) => void;
    selected: string | string[];
    onToggle: (id: string) => void;
    multi?: boolean;
  }) {
    return (
      <div className="flex flex-col gap-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Pesquisar por nome ou email..."
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            className="pl-9 shadow-none"
          />
        </div>
        <div className="border rounded-md overflow-y-auto h-48">
          {loadingProfessors ? (
            <div className="p-3 text-sm text-muted-foreground">A carregar...</div>
          ) : items.length === 0 ? (
            <div className="p-3 text-sm text-muted-foreground">Nenhum resultado.</div>
          ) : (
            items.map((p) => {
              const isSelected = multi ? (selected as string[]).includes(p.id) : selected === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => onToggle(p.id)}
                  className={cn(
                    "px-3 py-2 cursor-pointer text-sm hover:bg-muted transition-colors",
                    isSelected && "bg-primary/10 font-medium text-primary",
                  )}
                >
                  <div>{formatName(p)}</div>
                  {p.email && <div className="text-xs text-muted-foreground">{p.email}</div>}
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  }

  const lockedRegentProfessor = lockRegente ? professors.find((p) => p.id === initialRegente) : undefined;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
      {!isEdit && (
        <div>
          <label className="text-sm font-medium flex items-center gap-1 mb-1.5">
            Nome <span className="text-red-500">*</span>
          </label>
          <Controller
            control={control}
            name="nome"
            render={({ field }) => (
              <Input
                {...field}
                placeholder="Nome da UC"
                autoComplete="off"
                autoFocus
                className={cn(
                  "shadow-none",
                  formState.touchedFields.nome &&
                    (!field.value || field.value.trim() === "") &&
                    "border-red-500",
                )}
              />
            )}
          />
        </div>
      )}

      <div className="flex gap-6">
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-sm font-medium flex items-center gap-1">
            Regente <span className="text-red-500">*</span>
          </label>
          {lockRegente ? (
            <div className="border rounded-md px-3 py-2.5 text-sm bg-muted/50 text-muted-foreground select-none">
              {lockedRegentProfessor ? (
                <>
                  <div className="font-medium text-foreground">{formatName(lockedRegentProfessor)}</div>
                  {lockedRegentProfessor.email && (
                    <div className="text-xs">{lockedRegentProfessor.email}</div>
                  )}
                </>
              ) : (
                initialRegente || "—"
              )}
            </div>
          ) : (
            <Controller
              control={control}
              name="regente"
              render={({ field }) => (
                <SearchableList
                  items={filteredRegente}
                  search={regenteSearch}
                  onSearch={setRegenteSearch}
                  selected={field.value}
                  onToggle={(id) => field.onChange(field.value === id ? "" : id)}
                />
              )}
            />
          )}
        </div>

        <div className="flex-1 flex flex-col gap-2">
          <label className="text-sm font-medium">Professores</label>
          <Controller
            control={control}
            name="professores"
            render={({ field }) => (
              <SearchableList
                items={filteredProfessores}
                search={professoresSearch}
                onSearch={setProfessoresSearch}
                selected={field.value}
                onToggle={(id) =>
                  field.onChange(
                    field.value.includes(id)
                      ? field.value.filter((v) => v !== id)
                      : [...field.value, id],
                  )
                }
                multi
              />
            )}
          />
        </div>
      </div>

      <div className="flex gap-3">
        <Button
          type="button"
          variant="destructive"
          className="cursor-pointer"
          onClick={() => { reset(); onCancel?.(); }}
        >
          Cancelar
        </Button>
        <Button
          type="submit"
          className="cursor-pointer"
          disabled={
            (!isEdit && (!watch("nome") || watch("nome").trim() === "")) ||
            !watch("regente") ||
            (isEdit && watch("regente") === initialRegente && watch("professores").slice().sort().join(",") === initialProfessores.slice().sort().join(","))
          }
        >
          {isEdit ? "Guardar" : "Criar"}
        </Button>
      </div>
    </form>
  );
}

function EditUCFormLoader({ ucId, onSuccess, onCancel, lockRegente }: { ucId: number; onSuccess?: () => void; onCancel?: () => void; lockRegente?: boolean }) {
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(ucId);
  const { data: professors, isLoading: loadingProfs } = useGetUcProfessors(ucId);

  if (loadingRegent || loadingProfs) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" /></div>;
  }

  return (
    <UCFormInner
      key={`${ucId}-${regent?.id}-${professors?.map((p) => p.id).join(",")}`}
      ucId={ucId}
      initialRegente={regent?.id}
      initialProfessores={professors?.map((p) => p.id)}
      onSuccess={onSuccess}
      onCancel={onCancel}
      lockRegente={lockRegente}
    />
  );
}

export function NovaUCForm(props: UCFormProps = {}) {
  if (props.ucId) return <EditUCFormLoader ucId={props.ucId} onSuccess={props.onSuccess} onCancel={props.onCancel} lockRegente={props.lockRegente} />;
  return <UCFormInner {...props} />;
}
