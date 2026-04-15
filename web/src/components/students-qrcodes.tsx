import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CustomTable } from "@/components/custom-table";
import { Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useGetWarnings, useResolveWarnings } from "@/hooks/use-waiting-rooms";

const MOCK_URL =
  "https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=test3";

const MOCK_ALL_STUDENTS = [
  { id: "112903", name: "Marta", nmec: "112903", email: "marta@example.com" },
  { id: "112904", name: "Maria", nmec: "112904", email: "maria@example.com" },
  { id: "112905", name: "Joana", nmec: "112905", email: "joana@example.com" },
  { id: "112906", name: "Manel", nmec: "112906", email: "manel@example.com" },
  { id: "112907", name: "Goni", nmec: "112907", email: "goni@example.com" },
  { id: "112908", name: "Pedro", nmec: "112908", email: "pedro@example.com" },
  { id: "112909", name: "Ana", nmec: "112909", email: "ana@example.com" },
  { id: "112910", name: "Bruno", nmec: "112910", email: "bruno@example.com" },
  { id: "112911", name: "Carla", nmec: "112911", email: "carla@example.com" },
  { id: "112912", name: "David", nmec: "112912", email: "david@example.com" },
];

type Student = (typeof MOCK_ALL_STUDENTS)[number];

function StudentPickerDialog({
  open,
  assigned,
  onAdd,
  onClose,
}: {
  open: boolean;
  assigned: string[];
  onAdd: (s: Student) => void;
  onClose: () => void;
}) {
  const [selection, setSelection] = useState<Record<string, string>[]>([]);
  const available = MOCK_ALL_STUDENTS.filter((s) => !assigned.includes(s.id));

  const handleConfirm = () => {
    if (selection.length > 0) {
      onAdd(selection[0] as Student);
      setSelection([]);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Selecionar aluno</DialogTitle>
        </DialogHeader>
        <CustomTable
          isSelectable
          data={available}
          rowNumber={5}
          rowSelection={selection}
          onChange={(rows) => setSelection(rows.slice(-1))}
        />
        <Button
          disabled={selection.length === 0}
          onClick={handleConfirm}
          className="cursor-pointer"
        >
          Confirmar
        </Button>
      </DialogContent>
    </Dialog>
  );
}

type BlockState = {
  selected: string | null;
  removed: string[];
  extra: Student[];
};

export default function StudentsQRCodes({ wrId }: { wrId: number }) {
  const { data: warnings } = useGetWarnings(wrId);
  const { mutate: resolveWarnings } = useResolveWarnings(wrId);

  const [blockState, setBlockState] = useState<Record<number, BlockState>>({});
  const [pickerOpen, setPickerOpen] = useState<number | null>(null);

  const getState = (examId: number): BlockState =>
    blockState[examId] ?? { selected: null, removed: [], extra: [] };

  const updateState = (examId: number, patch: Partial<BlockState>) =>
    setBlockState((prev) => ({
      ...prev,
      [examId]: { ...getState(examId), ...patch },
    }));

  const allAssigned = warnings?.flatMap((qr) => {
    const s = getState(qr.exam_id);
    return [
      ...qr.students
        .map((st) => st.nmec.toString())
        .filter((n) => !s.removed.includes(n)),
      ...s.extra.map((e) => e.nmec),
    ];
  });

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {warnings && warnings.length > 0 && (
        <p className="text-sm text-muted-foreground mb-4 shrink-0">
          Alguns erros ocorreram durante o scan dos testes. Por favor selecione
          o aluno correspondente a cada teste para uma atribuição automática das
          notas.
        </p>
      )}

      <div className="flex-1 overflow-y-auto flex flex-col gap-6 pr-1">
        {warnings?.length === 0 ? (
          <p className="text-center text-muted-foreground py-12">
            Não existem problemas de associação.
          </p>
        ) : (
          warnings?.map((qr) => {
            const s = getState(qr.exam_id);
            const students = [
              ...qr.students
                .filter((st) => !s.removed.includes(st.nmec.toString()))
                .map((st) => ({
                  id: st.nmec.toString(),
                  name: st.name,
                  nmec: st.nmec.toString(),
                  email: st.email,
                })),
              ...s.extra,
            ];

            return (
              <div key={qr.exam_id} className="flex flex-col gap-2">
                <Card className="flex flex-row gap-6 p-4 items-start">
                  <div className="flex flex-col gap-2 items-center">
                    <img
                      src={MOCK_URL}
                      alt={`QR Code ${qr.exam_id}`}
                      className="w-28 h-28 shrink-0 rounded"
                    />
                    <span>Id Teste: {qr.exam_id}</span>
                  </div>

                  <div className="flex-1 flex flex-col gap-2">
                    {students.map((st) => (
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
                          <span className="font-medium text-sm">{st.name}</span>
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
                              selected:
                                s.selected === st.id ? null : s.selected,
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
                      assigned={allAssigned || []}
                      onAdd={(st) =>
                        updateState(qr.exam_id, { extra: [...s.extra, st] })
                      }
                      onClose={() => setPickerOpen(null)}
                    />
                  </div>
                </Card>
              </div>
            );
          })
        )}
        <Button
          className="self-end cursor-pointer"
          disabled={!warnings?.some((qr) => getState(qr.exam_id).selected)}
          onClick={() =>
            resolveWarnings({
              assignments: (warnings ?? [])
                .filter((qr) => getState(qr.exam_id).selected)
                .map((qr) => ({
                  exam_id: qr.exam_id,
                  student_nmec: getState(qr.exam_id).selected as string,
                })),
            })
          }
        >
          Associar
        </Button>
      </div>
    </div>
  );
}
