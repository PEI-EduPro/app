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
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page={roomDetails?.subject_name || "Scan de Exames"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />
      <div className="font-rubik flex justify-center text-lg md:text-5xl mb-7 md:mb-25">
        <span className="font-rubik">
          {roomDetails?.subject_name || "Carregando..."}
        </span>
      </div>

      <div className="flex flex-col gap-15 items-center">
        {isLoading ? (
          <div className="flex justify-center items-center w-full h-40">
            <LoaderCircle className="animate-spin size-16" />
          </div>
        ) : (
          <div className="flex flex-col justify-center gap-10 md:w-full">
            {roomDetails?.role === "regent" && (
              <div className="flex flex-row justify-between items-center">
                {metrics && (
                  <span className="text-sm font-medium">
                    {metrics.associated_students_count}/
                    {roomDetails.total_exams}
                  </span>
                )}
                {roomDetails?.state == "running" ? (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button className="cursor-pointer h-auto w-auto px-4 py-2 bg-red-500 border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                        <span className="w-fit font-medium">Fechar Exame</span>
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
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
                          className="cursor-pointer text-xl"
                        >
                          Cancelar
                        </AlertDialogCancel>
                        <AlertDialogAction
                          variant="destructive"
                          className="cursor-pointer text-xl"
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
                    className="cursor-pointer h-auto w-auto px-4 py-2 bg-green-500 border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none"
                    onClick={() => startRoom()}
                  >
                    <span className="w-fit font-medium">Abrir Exame</span>
                  </Button>
                )}
              </div>
            )}
            <div className="relative flex flex-row justify-center">
              {canAssociate && (
                <button
                  className="absolute top-21 left-1/2 -translate-x-1/2 z-10 bg-white rounded-full p-2 shadow-md cursor-pointer"
                  onClick={() => {
                    setCanAssociate(false);
                    setQRCode("");
                  }}
                >
                  <RotateCcw className="size-5" />
                </button>
              )}
              <Scanner
                onScan={(e) => {
                  setCanAssociate(true);
                  setQRCode(e[0].rawValue);
                }}
                paused={canAssociate || roomDetails?.state !== "running"}
                formats={["qr_code"]}
                styles={{
                  container: {
                    width: "70%",
                    aspectRatio: "1 / 1",
                    border: "2px dashed rgba(239, 68, 68, 0.4)",
                    borderRadius: "0.5rem",
                  },
                }}
                components={{
                  finder: false,
                }}
              />
            </div>
            <div className="md:w-full flex flex-1 flex-col">
              <span className="text-[26px] font-medium">Alunos</span>
              <CustomTable
                data={studentsData}
                rowNumber={15}
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
                    (el) => el.nmec != alunosSelection?.nmec,
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
            <Button
              className="cursor-pointer h-auto w-auto px-4 py-4.5 bg-[#2E2B50] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none"
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
              <span className="w-fit font-medium text-[26px]">
                Associar aluno
              </span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
