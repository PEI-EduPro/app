import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { createFileRoute } from "@tanstack/react-router";
import z from "zod";
import { Button } from "@/components/ui/button";
import { decodeId } from "@/lib/id-encoder";
import { RefreshCw, X, Camera } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import Webcam from "react-webcam";
import { toast } from "sonner";
import { useGetWaitingRoomById } from "@/hooks/use-waiting-rooms";

const detalheUCSearchSchema = z.object({
  ucId: z.string(),
});

export const Route = createFileRoute("/_layout/mobile_evaluate_tests")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function CameraCapture({
  setCapturedImage,
  capturedImage,
}: {
  setCapturedImage: (imageSrc: string | null) => void;
  capturedImage: string | null;
}) {
  const webcamRef = useRef<Webcam>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) setCapturedImage(imageSrc);
  }, [setCapturedImage]);

  if (cameraError) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 w-full h-64 rounded-2xl border-2 border-dashed border-destructive/40 bg-destructive/5 text-destructive text-sm px-4 text-center">
        <X className="w-8 h-8" />
        <span>{cameraError}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center w-full gap-5">
      {capturedImage ? (
        <>
          <div className="relative w-full rounded-2xl overflow-hidden shadow-xl ring-2 ring-[#41B5C0]/50">
            <img
              src={capturedImage}
              alt="Captured"
              className="w-full object-cover h-64"
            />
            <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-[#41B5C0] text-white text-xs font-bold px-2.5 py-1 rounded-full shadow">
              <span className="w-1.5 h-1.5 rounded-full bg-white" />
              Foto capturada
            </div>
          </div>
          <Button
            variant="outline"
            className="flex items-center gap-2 cursor-pointer border-[#41B5C0]/50 text-[#3263A8] hover:bg-[#41B5C0]/10"
            onClick={() => setCapturedImage(null)}
          >
            <RefreshCw className="w-4 h-4" />
            Tirar novamente
          </Button>
        </>
      ) : (
        <>
          <div className="relative w-full rounded-2xl overflow-hidden shadow-lg ring-2 ring-[#41B5C0]/30">
            <Webcam
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={{ facingMode: "environment" }}
              onUserMediaError={() =>
                setCameraError(
                  "Não foi possível acessar a câmera. Verifique as permissões.",
                )
              }
              className="w-full h-64 object-cover"
            />
            <div className="absolute inset-4 pointer-events-none">
              <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-[#41B5C0] rounded-tl-sm" />
              <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-[#41B5C0] rounded-tr-sm" />
              <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-[#41B5C0] rounded-bl-sm" />
              <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-[#41B5C0] rounded-br-sm" />
            </div>
          </div>

          <button
            onClick={capture}
            className="relative w-18 h-18 rounded-full bg-white border-4 border-[#41B5C0] shadow-lg shadow-[#41B5C0]/30 hover:shadow-[#41B5C0]/50 active:scale-95 cursor-pointer flex items-center justify-center"
            aria-label="Tirar Foto"
          >
            <Camera className="w-7 h-7 text-[#41B5C0]" />
          </button>
        </>
      )}
    </div>
  );
}

function RouteComponent() {
  const { ucId } = Route.useSearch();
  const realId = decodeId(ucId);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  const { data: roomDetails } = useGetWaitingRoomById(realId);

  return (
    <div className="py-3.5 px-4 w-full flex flex-col min-h-screen animate-fade-in">
      <AppBreadcrumb
        page={roomDetails?.subject_name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />

      <div className="flex flex-col items-center flex-1 gap-4 animate-fade-in-up">
        <h1 className="font-rubik text-xl font-bold text-foreground text-center">
          {roomDetails?.subject_name || "Carregando..."}
        </h1>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#41B5C0]/15 border border-[#41B5C0]/30">
          <span className="w-2 h-2 rounded-full bg-[#41B5C0] animate-pulse" />
          <span className="text-sm font-semibold text-[#3263A8]">
            0/{roomDetails?.total_exams} exames
          </span>
        </div>

        <div className="w-full flex-1 flex flex-col items-center justify-center stagger-2 animate-fade-in-up">
          <CameraCapture
            capturedImage={capturedImage}
            setCapturedImage={setCapturedImage}
          />
        </div>
      </div>

      <div className="sticky bottom-0 w-full pb-6 pt-3 bg-background/95 backdrop-blur-sm border-t border-border/50">
        <Button
          className="w-full cursor-pointer h-auto py-4 text-lg font-semibold shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:-translate-y-px active:translate-y-0 disabled:opacity-40"
          onClick={() => {
            if (capturedImage) {
              toast.success("Exame adicionado com sucesso!", {
                position: "top-right",
              });
              setCapturedImage(null);
            }
          }}
          disabled={!capturedImage}
        >
          Adicionar Teste
        </Button>
      </div>
    </div>
  );
}
