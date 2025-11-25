import { Button } from "@/components/ui/button";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  return (
    <div className="flex flex-col gap-[120px] mt-[170px]">
      <h1 className="text-5xl font-semibold text-center mb-20">
        Bem-vind@ ao EduPro
      </h1>
      <div className="flex items-start justify-center gap-24 h-[360px]">
        <div className="flex flex-col items-center justify-between text-center h-full">
          <p className="text-2xl text-gray-700 leading-snug">
            Um sistema que gera e avalia <br /> unidades curriculares
          </p>
          <Button className="py-[21px] px-[84px] text-4xl h-auto">
            Log In
          </Button>
          <p className="text-lg text-gray-600">
            Ainda não tens conta?{" "}
            <a href="#" className="text-[#41B5C0] hover:underline">
              Cria uma nova
            </a>
          </p>
        </div>
        <img
          src="/logo.png"
          alt="EduPro logo"
          className="h-full w-auto object-contain"
        />
      </div>
    </div>
  );
}
