import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { MultiSelect } from "@/components/multi-select";
import { Smartphone } from "lucide-react";
import { useGetProfessors } from "@/hooks/use-users";
import { useKeycloak } from "@/hooks/use-keycloak";

export default function Step2Content() {
  const [vigilants, setVigilants] = useState<string[]>([]);
  const { data: professors } = useGetProfessors();
  const { keycloak } = useKeycloak();

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

  return (
    <div className="flex flex-col gap-4 text-sm text-muted-foreground">
      <p>
        Ao iniciar o exame, a sala de espera é aberta e os alunos ficam
        disponíveis para associação. A partir deste momento, os vigilantes podem
        começar a associar os alunos a exames.
      </p>
      <div className="flex items-center gap-2 text-xs text-[#3263A8] bg-[#3263A8]/5 border border-[#3263A8]/20 rounded-md px-3 py-2">
        <Smartphone className="h-4 w-4 shrink-0" />
        <span>Esta ação pode ser realizada a partir da aplicação móvel.</span>
      </div>
      <div className="flex flex-col gap-2">
        <Label>Professores Vigilantes</Label>
        <MultiSelect
          emptyIndicator="Nenhum resultado encontrado"
          value={vigilants}
          onValueChange={setVigilants}
          placeholder="Selecione os vigilantes"
          options={options}
          maxCount={7}
          popoverClassName="w-[var(--radix-popover-trigger-width)]"
        />
      </div>
      <Button className="self-start cursor-pointer">Iniciar Exame</Button>
    </div>
  );
}
