import { useGetProfessors } from "@/hooks/use-users";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { SearchableList } from "./searchable-list";
import { useForm, Controller } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CancelConfirmDialog } from "./cancel-confirm-dialog";
import { useAddUc, useUpdateUc } from "@/hooks/use-ucs";

type UCFormT = {
  nome: string;
  regente: string;
  professores: string[];
};

export interface UCFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
  ucId?: number;
  initialRegente?: string;
  initialProfessores?: string[];
  lockRegente?: boolean;
}

function formatName(p: {
  firstName?: string;
  lastName?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  email?: string;
}) {
  return p.firstName && p.lastName
    ? `${p.firstName} ${p.lastName}`
    : p.first_name && p.last_name
      ? `${p.first_name} ${p.last_name}`
      : p.username || p.email || "";
}

export function UCFormInner({
  onSuccess,
  onCancel,
  ucId,
  initialRegente = "",
  initialProfessores = [],
  lockRegente = false,
}: UCFormProps) {
  const isEdit = !!ucId;
  const { mutate: addUc } = useAddUc(onSuccess);
  const { mutate: updateUc } = useUpdateUc(ucId ?? 0);
  const { data: professors = [], isLoading: loadingProfessors } =
    useGetProfessors();
  const [regenteSearch, setRegenteSearch] = useState("");
  const [professoresSearch, setProfessoresSearch] = useState("");

  const { handleSubmit, control, reset, watch, formState } = useForm<UCFormT>({
    defaultValues: {
      nome: "",
      regente: initialRegente,
      professores: initialProfessores,
    },
  });

  const selectedRegente = watch("regente");
  const selectedProfessores = watch("professores");

  const filteredRegente = professors
    .filter((p) => !selectedProfessores.includes(p.id))
    .filter((p) => {
      const q = regenteSearch.toLowerCase();
      return (
        formatName(p).toLowerCase().includes(q) ||
        (p.email || "").toLowerCase().includes(q)
      );
    });

  const filteredProfessores = professors
    .filter((p) => p.id !== selectedRegente)
    .filter((p) => {
      const q = professoresSearch.toLowerCase();
      return (
        formatName(p).toLowerCase().includes(q) ||
        (p.email || "").toLowerCase().includes(q)
      );
    });

  const onSubmit = (formData: UCFormT) => {
    if (isEdit) {
      updateUc({
        regent_keycloak_id: formData.regente,
        professor_keycloak_ids: formData.professores,
      });
      onSuccess?.();
    } else {
      addUc({
        name: formData.nome,
        regent_keycloak_id: formData.regente,
        professor_keycloak_ids: formData.professores,
      });
      reset();
    }
  };

  const lockedRegentProfessor = lockRegente
    ? professors.find((p) => p.id === initialRegente)
    : undefined;

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
                  <div className="font-medium text-foreground">
                    {formatName(lockedRegentProfessor)}
                  </div>
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
                  allItems={professors}
                  search={regenteSearch}
                  onSearch={setRegenteSearch}
                  selected={field.value}
                  onToggle={(id) =>
                    field.onChange(field.value === id ? "" : id)
                  }
                  loading={loadingProfessors}
                />
              )}
            />
          )}
        </div>

        <div className="flex-1 flex flex-col gap-2">
          <label className="text-sm font-medium">Outros Docentes</label>
          <Controller
            control={control}
            name="professores"
            render={({ field }) => (
              <SearchableList
                items={filteredProfessores}
                allItems={professors}
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
                loading={loadingProfessors}
              />
            )}
          />
        </div>
      </div>

      <div className="flex gap-3">
        <CancelConfirmDialog
          onConfirm={() => {
            reset();
            onCancel?.();
          }}
          isDirty={
            isEdit
              ? watch("regente") !== initialRegente ||
                watch("professores").slice().sort().join(",") !==
                  initialProfessores.slice().sort().join(",")
              : true
          }
        />
        <Button
          type="submit"
          className="cursor-pointer"
          disabled={
            (!isEdit && (!watch("nome") || watch("nome").trim() === "")) ||
            !watch("regente") ||
            (isEdit &&
              watch("regente") === initialRegente &&
              watch("professores").slice().sort().join(",") ===
                initialProfessores.slice().sort().join(","))
          }
        >
          {isEdit ? "Guardar" : "Criar"}
        </Button>
      </div>
    </form>
  );
}
