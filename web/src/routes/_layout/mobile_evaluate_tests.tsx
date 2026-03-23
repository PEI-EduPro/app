import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { createFileRoute } from "@tanstack/react-router";
import z from "zod";
import { Button } from "@/components/ui/button";
import { decodeId } from "@/lib/id-encoder";
import { RefreshCw, X } from "lucide-react";
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

const VIDEO_CONSTRAINTS = {
  facingMode: { ideal: "environment" },
  width: { ideal: 1280 },
  height: { ideal: 720 },
};

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
    if (imageSrc) {
      setCapturedImage(imageSrc);
    }
  }, [setCapturedImage]);

  const retake = () => setCapturedImage(null);

  if (cameraError) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 w-full h-48 rounded-xl border border-dashed border-red-400 bg-red-50 text-red-500 text-sm px-4 text-center">
        <X className="w-6 h-6" />
        <span>{cameraError}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center h-full w-full max-w-sm justify-between py-10">
      {capturedImage ? (
        <>
          <img
            src={capturedImage}
            alt="Captured"
            className="w-full rounded-xl object-cover shadow-md"
          />
          <Button
            variant="outline"
            className="flex items-center gap-2 cursor-pointer"
            onClick={retake}
          >
            <RefreshCw className="w-4 h-4" />
            Tirar novamente
          </Button>
        </>
      ) : (
        <>
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={VIDEO_CONSTRAINTS}
            onUserMediaError={() =>
              setCameraError(
                "Não foi possível acessar a câmera. Verifique as permissões.",
              )
            }
            className="w-full rounded-xl shadow-md"
          />
          <button
            onClick={capture}
            className="relative w-20 h-20 rounded-full bg-white border-4 border-[#2E2B50] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:scale-95 transition-transform cursor-pointer
    after:content-[''] after:absolute after:inset-2 after:rounded-full after:bg-white after:border-2 after:border-[#2E2B50]/20"
            aria-label="Tirar Foto"
          />
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
    <div className="py-3.5 px-6 w-full min-h-screen flex flex-col">
      <AppBreadcrumb
        page={roomDetails?.subject_name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />

      <div className="flex flex-col items-center flex-1">
        <div className="font-rubik flex justify-center text-lg md:text-5xl mb-7">
          <span className="font-rubik">
            {roomDetails?.subject_name || "Carregando..."}
          </span>
        </div>

        <span className="text-sm font-medium mb-6">
          0/{roomDetails?.total_exams}
        </span>

        <div className="flex flex-col items-center justify-center flex-1 w-full">
          <CameraCapture
            capturedImage={capturedImage}
            setCapturedImage={setCapturedImage}
          />
        </div>
      </div>

      <div className="sticky bottom-0 w-full pb-6 pt-3 bg-white">
        <Button
          className="w-full cursor-pointer h-auto px-4 py-4.5 bg-[#2E2B50] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none"
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
          <span className="w-fit font-medium text-[26px]">Adicionar Teste</span>
        </Button>
      </div>
    </div>
  );
}
