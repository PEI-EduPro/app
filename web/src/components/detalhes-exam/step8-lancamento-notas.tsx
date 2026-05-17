import { useState } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import {
  EmailPreview,
  TOGGLE_OPTIONS,
  type ToggleKey,
} from "../cenas_pa_mail/email-preview.tsx";

export default function Step8Content() {
  const [options, setOptions] = useState<Record<ToggleKey, boolean>>({
    exam_capture: false,
    question_weights: false,
    red_green_cross_table: false,
    cumulative_score_table: false,
  });
  const [customText, setCustomText] = useState("");

  return (
    <div className="flex gap-8 h-[82vh]">
      <div className="flex flex-col gap-6 w-72 shrink-0">
        <div className="flex flex-col gap-4">
          {TOGGLE_OPTIONS.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <Label htmlFor={key}>{label}</Label>
              <Switch
                id={key}
                checked={options[key]}
                onCheckedChange={(v) =>
                  setOptions((prev) => ({ ...prev, [key]: v }))
                }
              />
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="custom-text">Texto personalizado</Label>
          <Textarea
            id="custom-text"
            placeholder="Adicione uma mensagem personalizada ao email..."
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            rows={4}
          />
        </div>

        <Button className="self-start cursor-pointer">Lançar Notas</Button>
        <Button variant="outline" className="self-start cursor-pointer">
          <Download className="h-4 w-4 mr-2" />
          Exportar Notas (.pdf)
        </Button>
      </div>

      <div className="flex-1 border rounded-lg p-4 overflow-auto bg-white custom-scrollbar">
        <p className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wide">
          Esta pré-visualização serve apenas para fins ilustrativos e não
          reflete necessariamente o conteúdo do email final enviado aos alunos,
          apenas o formato.
        </p>
        <EmailPreview options={options} customText={customText} />
      </div>
    </div>
  );
}
