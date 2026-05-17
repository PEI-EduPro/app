import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { createFileRoute } from "@tanstack/react-router";
import z from "zod";
import { Button } from "@/components/ui/button";
import { decodeId } from "@/lib/id-encoder";
import { RefreshCw, Camera } from "lucide-react";
import { useRef, useState } from "react";
import Webcam from "react-webcam";
import {
  useGetSubmittedExams,
  useGetExamSessionInfo,
  useSendExamsPhotos,
} from "@/hooks/use-exams";

const detalheUCSearchSchema = z.object({ ucId: z.string() });

export const Route = createFileRoute("/_layout/mobile_evaluate_tests")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({ ucId: decodeId(search.ucId) }),
});

function CameraCapture({
  photo,
  onCapture,
  onRetake,
}: {
  photo: string | null;
  onCapture: (src: string) => void;
  onRetake: () => void;
}) {
  const webcamRef = useRef<Webcam>(null);

  if (photo) {
    return (
      <>
        <div className="relative w-full rounded-2xl overflow-hidden shadow-xl ring-2 ring-[#41B5C0]/50">
          <img src={photo} alt="Foto" className="w-full object-cover h-64" />
        </div>
        <Button
          variant="outline"
          className="w-full flex items-center gap-2 cursor-pointer border-[#41B5C0]/50 text-[#3263A8] hover:bg-[#41B5C0]/10"
          onClick={onRetake}
        >
          <RefreshCw className="w-4 h-4" />
          Tirar novamente
        </Button>
      </>
    );
  }

  return (
    <>
      <div className="relative w-full rounded-2xl overflow-hidden shadow-lg ring-2 ring-[#41B5C0]/30">
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          screenshotQuality={1}
          forceScreenshotSourceSize={true}
          videoConstraints={{
            width: 3840,
            height: 2160,
            facingMode: "environment",
          }}
          className="w-full h-64 object-cover"
        />
      </div>
      <button
        onClick={() => {
          const src = webcamRef.current?.getScreenshot();
          if (src) onCapture(src);
        }}
        className="w-18 h-18 rounded-full bg-white border-4 border-[#41B5C0] shadow-lg active:scale-95 cursor-pointer flex items-center justify-center"
        aria-label="Tirar Foto"
      >
        <Camera className="w-7 h-7 text-[#41B5C0]" />
      </button>
    </>
  );
}

function RouteComponent() {
  const { ucId } = Route.useSearch();
  const realId = decodeId(ucId);
  const [photo, setPhoto] = useState<string | null>(null);

  const { data: roomDetails } = useGetExamSessionInfo(realId);
  const { mutate } = useSendExamsPhotos(realId);
  const { data: submitedExams } = useGetSubmittedExams(realId);

  return (
    <div className="py-3.5 px-4 w-full flex flex-col min-h-screen">
      <AppBreadcrumb
        page={roomDetails?.subject_name || "Detalhes"}
        crumbs={[{ name: "Exames", link: "/unidades-curriculares" }]}
      />

      <div className="flex flex-col items-center flex-1 gap-4">
        <h1 className="font-rubik text-xl font-bold text-foreground text-center">
          {roomDetails?.subject_name || "Carregando..."}
        </h1>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#41B5C0]/15 border border-[#41B5C0]/30">
          <span className="w-2 h-2 rounded-full bg-[#41B5C0] animate-pulse" />
          <span className="text-sm font-semibold text-[#3263A8]">
            {submitedExams?.submitted_count || 0}/{roomDetails?.total_exams}{" "}
            exames
          </span>
        </div>

        <div className="w-full flex flex-col items-center gap-4">
          <CameraCapture
            photo={photo}
            onCapture={setPhoto}
            onRetake={() => setPhoto(null)}
          />
        </div>
      </div>

      <div className="sticky bottom-0 w-full pb-6 pt-3 bg-background/95 backdrop-blur-sm border-t border-border/50">
        <Button
          className="w-full cursor-pointer h-auto py-4 text-lg font-semibold disabled:opacity-40"
          onClick={() => {
            mutate([photo!]);
            setPhoto(null);
          }}
          disabled={!photo}
        >
          Enviar Testes
        </Button>
      </div>
    </div>
  );
}
