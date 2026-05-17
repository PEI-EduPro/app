import { Button } from "@/components/ui/button";
import { Smartphone } from "lucide-react";

export default function Step2Content() {
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
      <Button className="self-start cursor-pointer">Iniciar Exame</Button>
    </div>
  );
}
