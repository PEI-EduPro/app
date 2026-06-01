import { Button } from "@/components/ui/button";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useKeycloak } from "@/hooks/use-keycloak";
import { usePwaInstall } from "@/hooks/use-pwa-install";
import { Download } from "lucide-react";
import { useIsMobile } from "@/hooks/use-mobile";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  const { keycloak } = useKeycloak();
  const { canInstall, install } = usePwaInstall();
  const isMobile = useIsMobile();

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#2E2B50] flex flex-col items-center justify-center px-4">
      <div className="pointer-events-none absolute -top-32 -left-32 w-96 h-96 rounded-full bg-[#41B5C0] opacity-20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-[#3263A8] opacity-30 blur-3xl" />
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-150 h-150 rounded-full bg-[#9EE78F] opacity-5 blur-3xl" />

      <div className="relative z-10 flex flex-col md:flex-row items-center gap-12 md:gap-24 max-w-5xl w-full">
        <div className="flex flex-col items-center md:items-start gap-6 text-center md:text-left animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#41B5C0]/20 border border-[#41B5C0]/40 stagger-1 animate-fade-in-up">
            <span className="w-2 h-2 rounded-full bg-[#9EE78F] animate-pulse" />
            <span className="text-[#9EE78F] text-sm font-medium">
              Plataforma de Avaliação
            </span>
          </div>

          <h1 className="font-rubik text-4xl md:text-6xl font-bold text-white leading-tight stagger-2 animate-fade-in-up">
            Bem-vind@ ao <span className="text-[#41B5C0]">EduPro</span>
          </h1>

          <p className="text-[#E3F6A2]/80 text-lg md:text-xl leading-relaxed max-w-md stagger-3 animate-fade-in-up">
            Um sistema que gera e avalia exames <br /> de unidades curriculares
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 stagger-4 animate-fade-in-up">
            <Link to="/unidades-curriculares">
              <Button
                className="px-8 py-4 text-lg h-auto cursor-pointer bg-[#41B5C0] hover:bg-[#41B5C0]/90 text-white shadow-lg shadow-[#41B5C0]/30 hover:shadow-[#41B5C0]/50 hover:-translate-y-0.5 active:translate-y-0"
                onClick={() =>
                  keycloak.login({
                    redirectUri: `${window.location.origin}${import.meta.env.BASE_URL}unidades-curriculares`
                  })
                }
              >
                Entrar
              </Button>
            </Link>

            <p className="text-[#E3F6A2]/60 text-sm">
              Ainda não tens conta?{" "}
              <a
                href="#"
                className="text-[#9EE78F] hover:text-[#E3F6A2] underline underline-offset-2"
                onClick={(e) => {
                  e.preventDefault();
                  keycloak.register({
                    redirectUri: `${window.location.origin}${import.meta.env.BASE_URL}unidades-curriculares`
                  });
                }}
              >
                Cria uma nova
              </a>
            </p>
          </div>

          {canInstall && isMobile && (
            <Button
              variant="outline"
              className="flex items-center gap-2 cursor-pointer border-[#41B5C0]/50 text-[#41B5C0] hover:bg-[#41B5C0]/10"
              onClick={install}
            >
              <Download className="w-4 h-4" />
              Instalar aplicação
            </Button>
          )}
        </div>

        <div className="animate-float shrink-0">
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-[#41B5C0]/20 blur-2xl scale-110" />
            <img
              src={`${import.meta.env.BASE_URL}logo.png`}
              alt="EduPro logo"
              className="relative w-48 h-48 md:w-72 md:h-72 object-contain drop-shadow-2xl"
            />
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-linear-to-t from-[#2E2B50] to-transparent" />
    </div>
  );
}
