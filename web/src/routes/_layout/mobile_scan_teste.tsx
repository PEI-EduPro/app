import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Scanner } from "@yudiel/react-qr-scanner";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LoaderCircle, RotateCcw, TriangleAlert } from "lucide-react";
import { useState } from "react";
import z from "zod";
import { Button } from "@/components/ui/button";
import { decodeId } from "@/lib/id-encoder";
import {
  useCloseExamSession,
  useGetExamSessionInfo,
  useGetExamSessionMetrics,
  usePostPairExamStudent,
  useStartExamSession,
} from "@/hooks/use-exams";
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

  const { data: roomDetails, isLoading } = useGetExamSessionInfo(realId);

  const { data: metrics } = useGetExamSessionMetrics({
    enabled: roomDetails?.role === "regent",
    examConfigId: realId,
    refetchInterval: 5000,
  });

  const { mutate: postExamStudent } = usePostPairExamStudent(realId);
  const { mutate: closeRoom } = useCloseExamSession(realId);
  const { mutate: startRoom } = useStartExamSession(realId);

  const [canAssociate, setCanAssociate] = useState<boolean>(false);
  const [QRCode, setQRCode] = useState<string>("");

  const studentsData = roomDetails?.student_list.map((s) => ({
    id: s.nmec,
    nmec: s.nmec,
    nome: s.name,
  })) as unknown as Record<string, string>[];

  const examClosed =
    !isLoading &&
    roomDetails &&
    roomDetails.state !== "running" &&
    roomDetails.state !== "preparing";

  if (examClosed) {
    navigate({ to: "/mobile_evaluate_tests", search: { ucId } });
    return null;
  }

  const examNotOpen =
    !isLoading && roomDetails && roomDetails.state === "preparing";

  return (
    <div
      className="h-dvh flex flex-col py-2 px-4 w-full animate-fade-in overflow-x-hidden text-xs [&_h1]:text-base [&_span]:text-xs [&_button]:text-xs [&_input]:text-xs"
      onClick={(e) => e.stopPropagation()}
    >
      <AlertDialog open={!!examNotOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Exame ainda não aberto</AlertDialogTitle>
            <AlertDialogDescription>
              O exame ainda não foi aberto. É necessário abrir o exame para
              começar com a associação de alunos e o exame aparecer nos
              dispositivos dos restantes professores vigilantes.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogAction
              size="lg"
              className="w-full cursor-pointer bg-[#41B5C0] hover:bg-[#41B5C0]/80"
              onClick={() => startRoom()}
            >
              Iniciar Exame
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AppBreadcrumb
        page={roomDetails?.subject_name || "Scan de Exames"}
        crumbs={[{ name: "Exames", link: "/unidades-curriculares" }]}
      />

      <h1 className="font-rubik text-center text-base font-bold text-foreground mb-2 animate-fade-in-up truncate">
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
                <div onClick={(e) => e.stopPropagation()}>
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
                          <TriangleAlert />
                        </AlertDialogMedia>
                        <AlertDialogTitle>Fechar Exame</AlertDialogTitle>
                        <AlertDialogDescription>
                          Ao fechar o exame nenhum outro utilizador conseguirá
                          fazer scan a mais nenhum código QR. Deseja continuar?
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                        <AlertDialogCancel
                          variant="outline"
                          size="lg"
                          className="cursor-pointer"
                        >
                          Cancelar
                        </AlertDialogCancel>
                        <AlertDialogAction
                          variant="destructive"
                          size="lg"
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
                </div>
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
              <div className="flex-1 min-h-0 overflow-auto max-w-full [&_table]:text-xs [&_th]:px-1 [&_td]:px-1 [&_button]:px-1 [&_button]:text-xs [&_th]:whitespace-normal [&_td]:whitespace-normal [&_.relative.w-full.overflow-x-auto]:overflow-x-hidden">
                <CustomTable
                  data={studentsData}
                  rowNumber={3}
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
