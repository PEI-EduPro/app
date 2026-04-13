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
import { useGetWarnings } from "@/hooks/use-waiting-rooms";

const MOCK_QRCODES = [
  {
    id: 1,
    imageUrl:
      "https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=test1",
    studentIds: ["112903", "112904"],
  },
  {
    id: 2,
    imageUrl:
      "https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=test2",
    studentIds: [] as string[],
  },
  {
    id: 3,
    imageUrl:
      "https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=test3",
    studentIds: ["112906"],
  },
];

const MOCK_ALL_STUDENTS = [
  { id: "112903", nome: "Marta", nmec: "112903" },
  { id: "112904", nome: "Maria", nmec: "112904" },
  { id: "112905", nome: "Joana", nmec: "112905" },
  { id: "112906", nome: "Manel", nmec: "112906" },
  { id: "112907", nome: "Goni", nmec: "112907" },
  { id: "112908", nome: "Pedro", nmec: "112908" },
  { id: "112909", nome: "Ana", nmec: "112909" },
  { id: "112910", nome: "Bruno", nmec: "112910" },
  { id: "112911", nome: "Carla", nmec: "112911" },
  { id: "112912", nome: "David", nmec: "112912" },
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

export default function StudentsQRCodes({ wrId }: { wrId: number }) {
  const { data: warnings } = useGetWarnings(wrId);

  console.log("Warnings:", warnings);

  const [blocks, setBlocks] = useState(
    MOCK_QRCODES.map((qr) => ({
      qr,
      students: MOCK_ALL_STUDENTS.filter((s) =>
        qr.studentIds.includes(s.id),
      ) as Student[],
      selected: null as string | null,
      pickerOpen: false,
    })),
  );

  const allAssigned = blocks.flatMap((b) => b.students.map((s) => s.id));

  const toggle = (blockIdx: number, id: string) => {
    setBlocks((prev) =>
      prev.map((b, i) =>
        i === blockIdx ? { ...b, selected: b.selected === id ? null : id } : b,
      ),
    );
  };

  const addStudent = (blockIdx: number, student: Student) => {
    setBlocks((prev) =>
      prev.map((b, i) =>
        i === blockIdx ? { ...b, students: [...b.students, student] } : b,
      ),
    );
  };

  const removeStudent = (blockIdx: number, id: string) => {
    setBlocks((prev) =>
      prev.map((b, i) =>
        i === blockIdx
          ? {
              ...b,
              students: b.students.filter((s) => s.id !== id),
              selected: b.selected === id ? null : b.selected,
            }
          : b,
      ),
    );
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {blocks.length > 0 && (
        <p className="text-sm text-muted-foreground mb-4 shrink-0">
          Alguns erros ocorreram durante o scan dos testes. Por favor selecione
          o aluno correspondente a cada teste para uma atribuição automática das
          notas.
        </p>
      )}

      <div className="flex-1 overflow-y-auto flex flex-col gap-6 pr-1">
        {blocks.length === 0 ? (
          <p className="text-center text-muted-foreground py-12">
            Não existem problemas de associação.
          </p>
        ) : (
          blocks.map((block, idx) => (
            <div key={block.qr.id} className="flex flex-col gap-2">
              <Card className="flex flex-row gap-6 p-4 items-start">
                <div className="flex flex-col gap-2 items-center">
                  <img
                    src={block.qr.imageUrl}
                    alt={`QR Code ${block.qr.id}`}
                    className="w-28 h-28 shrink-0 rounded"
                  />
                  <span>Id Teste: {block.qr.id}</span>
                </div>

                <div className="flex-1 flex flex-col gap-2">
                  {block.students.map((s) => (
                    <div key={s.id} className="flex items-center gap-1">
                      <Button
                        variant="outline"
                        onClick={() => toggle(idx, s.id)}
                        className={cn(
                          "flex-1 justify-start gap-3 border transition-colors cursor-pointer",
                          block.selected === s.id
                            ? "border-[#3263A8] bg-[#3263A8]/10"
                            : "border-border",
                        )}
                      >
                        <span className="font-medium text-sm">{s.nome}</span>
                        <span className="text-xs text-muted-foreground">
                          {s.nmec}
                        </span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="shrink-0 text-muted-foreground hover:text-destructive hover:bg-red-50 cursor-pointer"
                        onClick={() => removeStudent(idx, s.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}

                  <Button
                    variant="ghost"
                    className="self-start flex items-center gap-1 text-sm text-[#3263A8] px-0 cursor-pointer"
                    onClick={() =>
                      setBlocks((prev) =>
                        prev.map((b, i) => ({ ...b, pickerOpen: i === idx })),
                      )
                    }
                  >
                    <Plus className="h-4 w-4" /> Adicionar aluno
                  </Button>

                  <StudentPickerDialog
                    open={block.pickerOpen}
                    assigned={allAssigned}
                    onAdd={(s) => addStudent(idx, s)}
                    onClose={() =>
                      setBlocks((prev) =>
                        prev.map((b, i) =>
                          i === idx ? { ...b, pickerOpen: false } : b,
                        ),
                      )
                    }
                  />
                </div>
              </Card>

              <Button
                className="self-end cursor-pointer"
                disabled={block.selected === null}
              >
                Associar
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
