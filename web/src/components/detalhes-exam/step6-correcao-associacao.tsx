import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CustomTable } from "@/components/custom-table";
import { Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import QRCode from "react-qr-code";

const MOCK_STUDENTS = [
  { nmec: 12345, name: "Ana Silva", email: "ana.silva@ua.pt" },
  { nmec: 12346, name: "Bruno Costa", email: "bruno.costa@ua.pt" },
  { nmec: 12347, name: "Carla Mendes", email: "carla.mendes@ua.pt" },
  { nmec: 12348, name: "David Ferreira", email: "david.ferreira@ua.pt" },
  { nmec: 12349, name: "Eva Rodrigues", email: "eva.rodrigues@ua.pt" },
  { nmec: 12350, name: "Fábio Santos", email: "fabio.santos@ua.pt" },
  { nmec: 12351, name: "Gabriela Lima", email: "gabriela.lima@ua.pt" },
  { nmec: 12352, name: "Hugo Pereira", email: "hugo.pereira@ua.pt" },
  { nmec: 12353, name: "Inês Oliveira", email: "ines.oliveira@ua.pt" },
  { nmec: 12354, name: "João Martins", email: "joao.martins@ua.pt" },
];

const MOCK_WARNINGS = Array.from({ length: 10 }, (_, i) => ({
  exam_id: 101 + i,
  batch_number: (i % 3) + 1,
  students: [MOCK_STUDENTS[i]],
}));

type StudentRow = { id: string; nome: string; nmec: string; email: string };
type BlockState = {
  selected: string | null;
  removed: string[];
  extra: StudentRow[];
};

function StudentPickerDialog({
  open,
  assigned,
  onAdd,
  onClose,
}: {
  open: boolean;
  assigned: string[];
  onAdd: (s: StudentRow) => void;
  onClose: () => void;
}) {
  const [selection, setSelection] = useState<StudentRow[]>([]);
  const available: StudentRow[] = MOCK_STUDENTS.filter(
    (s) => !assigned.includes(s.nmec.toString()),
  ).map((s) => ({
    id: s.nmec.toString(),
    nome: s.name,
    nmec: s.nmec.toString(),
    email: s.email,
  }));

  const handleConfirm = () => {
    if (selection.length > 0) {
      onAdd(selection[0]);
      setSelection([]);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Selecionar aluno</DialogTitle>
          <DialogDescription>
            Selecione o aluno a associar a este exame.
          </DialogDescription>
        </DialogHeader>
        <CustomTable
          isSelectable
          data={available}
          rowNumber={5}
          rowSelection={selection}
          onChange={(rows) => setSelection((rows as StudentRow[]).slice(-1))}
        />
        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            className="cursor-pointer"
          >
            Cancelar
          </Button>
          <Button
            disabled={selection.length === 0}
            onClick={handleConfirm}
            className="cursor-pointer"
          >
            Confirmar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Step6Content() {
  const [blockState, setBlockState] = useState<Record<number, BlockState>>({});
  const [pickerOpen, setPickerOpen] = useState<number | null>(null);

  const getState = (examId: number): BlockState =>
    blockState[examId] ?? { selected: null, removed: [], extra: [] };

  const updateState = (examId: number, patch: Partial<BlockState>) =>
    setBlockState((prev) => ({
      ...prev,
      [examId]: { ...getState(examId), ...patch },
    }));

  const allAssigned = MOCK_WARNINGS.flatMap((qr) => {
    const s = getState(qr.exam_id);
    return [
      ...qr.students
        .map((st) => st.nmec.toString())
        .filter((n) => !s.removed.includes(n)),
      ...s.extra.map((e) => e.nmec),
    ];
  });

  return (
    <div className="flex flex-col gap-6 shrink-0 overflow-y-auto custom-scrollbar max-h-[82vh]">
      <p className="text-sm text-muted-foreground">
        Alguns erros ocorreram durante o scan dos testes. Por favor selecione o
        aluno correspondente a cada teste.
      </p>

      {MOCK_WARNINGS.map((qr) => {
        const s = getState(qr.exam_id);
        const rows: StudentRow[] = [
          ...qr.students
            .filter((st) => !s.removed.includes(st.nmec.toString()))
            .map((st) => ({
              id: st.nmec.toString(),
              nome: st.name,
              nmec: st.nmec.toString(),
              email: st.email,
            })),
          ...s.extra,
        ];

        return (
          <Card
            key={qr.exam_id}
            className="flex flex-row gap-6 p-4 items-start"
          >
            <div className="flex flex-col gap-2 items-center">
              <QRCode value={qr.exam_id.toString()} size={72} level="M" />
              <span className="text-sm">Versão: {qr.batch_number}</span>
            </div>

            <div className="flex-1 flex flex-col gap-2">
              {rows.map((st) => (
                <div key={st.id} className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    onClick={() =>
                      updateState(qr.exam_id, {
                        selected: s.selected === st.id ? null : st.id,
                      })
                    }
                    className={cn(
                      "flex-1 justify-start gap-3 border transition-colors cursor-pointer",
                      s.selected === st.id
                        ? "border-[#3263A8] bg-[#3263A8]/10"
                        : "border-border",
                    )}
                  >
                    <span className="font-medium text-sm">{st.nome}</span>
                    <span className="text-xs text-muted-foreground">
                      {st.email}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {st.nmec}
                    </span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive hover:bg-red-50 cursor-pointer"
                    onClick={() =>
                      updateState(qr.exam_id, {
                        removed: [...s.removed, st.id],
                        selected: s.selected === st.id ? null : s.selected,
                        extra: s.extra.filter((e) => e.id !== st.id),
                      })
                    }
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}

              <Button
                variant="ghost"
                className="self-start flex items-center gap-1 text-sm text-[#3263A8] px-0 cursor-pointer"
                onClick={() => setPickerOpen(qr.exam_id)}
              >
                <Plus className="h-4 w-4" /> Adicionar aluno
              </Button>

              <StudentPickerDialog
                open={pickerOpen === qr.exam_id}
                assigned={allAssigned}
                onAdd={(st) =>
                  updateState(qr.exam_id, { extra: [...s.extra, st] })
                }
                onClose={() => setPickerOpen(null)}
              />
            </div>
          </Card>
        );
      })}

      <Button className="self-end cursor-pointer">Associar</Button>
    </div>
  );
}
