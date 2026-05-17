import { Button } from "@/components/ui/button";
import { Smartphone } from "lucide-react";

export default function Step4Content() {
  return (
    <div className="flex flex-col gap-4 text-sm text-muted-foreground">
      <p>
        Ao fechar o exame, deixa de ser possível realizar mais associações entre
        alunos e exames. Certifique-se de que todos os alunos presentes foram
        devidamente registados antes de prosseguir.
      </p>
      <div className="flex items-center gap-2 text-xs text-[#3263A8] bg-[#3263A8]/5 border border-[#3263A8]/20 rounded-md px-3 py-2">
        <Smartphone className="h-4 w-4 shrink-0" />
        <span>Esta ação pode ser realizada a partir da aplicação móvel.</span>
      </div>
      <Button variant="destructive" className="self-start cursor-pointer">
        Fechar Exame
      </Button>
    </div>
  );
}
