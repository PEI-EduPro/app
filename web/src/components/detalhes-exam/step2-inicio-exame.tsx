import { Button } from "@/components/ui/button";
import { Smartphone } from "lucide-react";
import { useState } from "react";
import { Label } from "@/components/ui/label";
import { MultiSelect } from "@/components/multi-select";
import { useGetProfessors } from "@/hooks/use-users";
import { useKeycloak } from "@/hooks/use-keycloak";
import { usePatchExamVigilants, useStartExamSession } from "@/hooks/use-exams";

export default function Step2Content({
  examConfigId,
  disabled,
  savedVigilants = [],
}: {
  examConfigId: number;
  disabled?: boolean;
  savedVigilants?: { id: string }[];
}) {
  const { data: professors } = useGetProfessors();
  const { keycloak } = useKeycloak();
  const startMutation = useStartExamSession(examConfigId);
  const patchVigilants = usePatchExamVigilants(examConfigId);

  const options =
    professors
      ?.map((p) => ({
        value: p.id,
        label:
          p.firstName && p.lastName
            ? `${p.firstName} ${p.lastName}`
            : p.username || p.id,
      }))
      .filter((e) => e.value !== keycloak.tokenParsed?.sub) ?? [];

  const savedIds = savedVigilants.map((v) => v.id);

  const [currentVigilants, setCurrentVigilants] = useState<string[]>(savedIds);

  const isDirty =
    currentVigilants.length !== savedIds.length ||
    currentVigilants.some((id) => !savedIds.includes(id));

  return (
    <div className="flex flex-col gap-4 text-sm text-muted-foreground">
      <p>
        Ao iniciar o exame, os alunos ficam disponíveis e os vigilantes poderam
        começar a associar os alunos a exames.
      </p>
      <div className="flex items-center gap-2 text-xs text-[#3263A8] bg-[#3263A8]/5 border border-[#3263A8]/20 rounded-md px-3 py-2">
        <Smartphone className="h-4 w-4 shrink-0" />
        <span>Esta ação pode ser realizada a partir da aplicação móvel.</span>
      </div>
      <div className="flex flex-col gap-2">
        <Label>Professores Vigilantes</Label>
        <MultiSelect
          disabled={disabled}
          emptyIndicator="Nenhum resultado encontrado"
          defaultValue={savedIds}
          onValueChange={setCurrentVigilants}
          placeholder="Selecione os vigilantes"
          options={options}
          maxCount={7}
          popoverClassName="w-[var(--radix-popover-trigger-width)]"
        />
      </div>
      <div className="flex gap-2">
        {isDirty && (
          <Button
            variant="outline"
            className="cursor-pointer"
            disabled={patchVigilants.isPending}
            onClick={() => patchVigilants.mutate(currentVigilants)}
          >
            Guardar Vigilantes
          </Button>
        )}
        <Button
          className="cursor-pointer"
          disabled={disabled || startMutation.isPending || isDirty}
          onClick={() => startMutation.mutate()}
        >
          Iniciar Exame
        </Button>
      </div>
    </div>
  );
}
