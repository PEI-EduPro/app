import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Scanner } from "@yudiel/react-qr-scanner";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LoaderCircle, RotateCcw, Trash2Icon } from "lucide-react";
import { useState } from "react";
import z from "zod";
import { Button } from "@/components/ui/button";
import { decodeId } from "@/lib/id-encoder";
import {
  useCloseWaitingRoom,
  useGetWaitingRoomById,
  useGetWaitingRoomMetrics,
  usePostPairExamStudent,
  useStartWaitingRoom,
} from "@/hooks/use-waiting-rooms";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const detalheUCSearchSchema = z.object({
  ucId: z.string(),
});

export const Route = createFileRoute("/_layout/mobile_scan_teste")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function RouteComponent() {
  const { ucId } = Route.useSearch();
  const realId = decodeId(ucId);
  const [alunosSelection, setAlunosSelection] = useState<{
    nome: string;
    nmec: string;
  }>();

  const navigate = useNavigate();

  const { data: roomDetails, isLoading } = useGetWaitingRoomById(realId);

  const { data: metrics } = useGetWaitingRoomMetrics({
    enabled: roomDetails?.role === "regent",
    roomId: realId,
    refetchInterval: 5000,
  });

  const { mutate: postExamStudent } = usePostPairExamStudent(realId);
  const { mutate: closeRoom } = useCloseWaitingRoom(realId);
  const { mutate: startRoom } = useStartWaitingRoom(realId);

  const [canAssociate, setCanAssociate] = useState<boolean>(false);
  const [QRCode, setQRCode] = useState<string>("");

  const studentsData = roomDetails?.student_list.map((s) => ({
    id: s.nmec,
    nmec: s.nmec,
    nome: s.name,
  })) as unknown as Record<string, string>[];

  return (
    <div className="h-dvh flex flex-col py-2 px-4 w-full animate-fade-in overflow-hidden">
      <AppBreadcrumb
        page={roomDetails?.subject_name || "Scan de Exames"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />

      <h1 className="font-rubik text-center text-lg font-bold text-foreground mb-2 animate-fade-in-up">
        {roomDetails?.subject_name || "Carregando..."}
      </h1>

      <div className="flex flex-col gap-3 items-center flex-1 min-h-0">
        {isLoading ? (
          <div className="flex justify-center items-center w-full h-40">
            <LoaderCircle className="animate-spin size-12 text-primary" />
          </div>
        ) : (
          <div className="flex flex-col gap-3 w-full flex-1 min-h-0 animate-fade-in-up stagger-1">
            {roomDetails?.role === "regent" && (
              <div className="flex flex-row justify-between items-center px-1">
                {metrics && (
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#41B5C0] animate-pulse" />
                    <span className="text-sm font-semibold text-foreground">
                      {metrics.associated_exams_count}/{roomDetails.total_exams}{" "}
                      exames associados
                    </span>
                  </div>
                )}
                {roomDetails?.state === "running" ? (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="destructive"
                        className="cursor-pointer h-auto px-4 py-2"
                      >
                        Fechar Exame
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogMedia className="bg-destructive/10 text-destructive">
                          <Trash2Icon />
                        </AlertDialogMedia>
                        <AlertDialogTitle className="font-medium text-xl">
                          Fechar Exame
                        </AlertDialogTitle>
                        <AlertDialogDescription className="font-medium">
                          Ao fechar o exame nenhum outro utilizador conseguirá
                          fazer scan a mais nenhum código QR. Deseja continuar?
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                        <AlertDialogCancel
                          variant="outline"
                          className="cursor-pointer"
                        >
                          Cancelar
                        </AlertDialogCancel>
                        <AlertDialogAction
                          variant="destructive"
                          className="cursor-pointer"
                          onClick={() => {
                            closeRoom();
                            navigate({
                              to: "/mobile_evaluate_tests",
                              search: { ucId },
                            });
                          }}
                        >
                          Continuar
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                ) : (
                  <Button
                    className="cursor-pointer h-auto px-4 py-2 bg-[#41B5C0] text-white hover:bg-[#41B5C0]/80 font-semibold"
                    onClick={() => startRoom()}
                  >
                    Abrir Exame
                  </Button>
                )}
              </div>
            )}

            <div className="relative flex flex-row justify-center">
              {canAssociate && (
                <button
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 bg-white rounded-full p-3 shadow-lg cursor-pointer hover:scale-110 active:scale-95"
                  onClick={() => {
                    setCanAssociate(false);
                    setQRCode("");
                  }}
                >
                  <RotateCcw className="size-5 text-[#2E2B50]" />
                </button>
              )}
              <div
                className={`rounded-2xl overflow-hidden transition-all duration-300 ${canAssociate ? "ring-4 ring-[#41B5C0]/80" : "ring-2 ring-[#41B5C0]/40"}`}
              >
                <Scanner
                  onScan={(e) => {
                    setCanAssociate(true);
                    setQRCode(e[0].rawValue);
                  }}
                  paused={canAssociate || roomDetails?.state !== "running"}
                  formats={["qr_code"]}
                  styles={{
                    container: {
                      width: "50vw",
                      maxWidth: "200px",
                      aspectRatio: "1 / 1",
                    },
                  }}
                  components={{ finder: false }}
                />
              </div>
            </div>

            <div className="flex justify-center">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${canAssociate ? "bg-[#41B5C0]/20 text-[#3263A8]" : "bg-[#41B5C0]/15 text-[#3263A8]"}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full bg-[#41B5C0]`} />
                {canAssociate
                  ? "QR Code lido — selecione um aluno"
                  : "Aguardando QR Code"}
              </span>
            </div>

            <div className="w-full flex flex-col gap-1 flex-1 min-h-0">
              <span className="text-base font-semibold text-foreground">
                Alunos
              </span>
              <div className="flex-1 min-h-0 overflow-auto">
                <CustomTable
                  data={studentsData}
                  rowNumber={5}
                  isSelectable
                  rowSelection={
                    alunosSelection
                      ? [
                          {
                            id: alunosSelection.nmec,
                            nmec: alunosSelection.nmec,
                            nome: alunosSelection.nome,
                          },
                        ]
                      : []
                  }
                  onChange={(e) => {
                    const newSelection = e.filter(
                      (el) => el.nmec !== alunosSelection?.nmec,
                    );
                    if (newSelection.length > 0) {
                      setAlunosSelection({
                        nome: newSelection[0].nome,
                        nmec: newSelection[0].nmec,
                      });
                    } else {
                      setAlunosSelection(undefined);
                    }
                  }}
                />
              </div>
            </div>

            <Button
              className="w-full cursor-pointer h-auto py-2.5 text-base font-semibold shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:-translate-y-px active:translate-y-0"
              disabled={
                roomDetails?.state === "running"
                  ? !canAssociate || alunosSelection === undefined
                  : true
              }
              onClick={() => {
                postExamStudent({
                  nmec: Number(alunosSelection?.nmec),
                  qr: QRCode,
                });
                setCanAssociate(false);
                setAlunosSelection(undefined);
              }}
            >
              Associar aluno
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
