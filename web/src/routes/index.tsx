import { Button } from "@/components/ui/button";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useKeycloak } from "@/hooks/use-keycloak";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  const { keycloak } = useKeycloak();

  return (
    <div className="flex flex-col items-center gap-8 md:gap-30 mt-10 md:mt-42.5 px-4 md:px-0">
      <h1 className="font-rubik text-3xl md:text-5xl font-semibold text-center mb-5 md:mb-20">
        Bem-vind@ ao EduPro
      </h1>

      <div className="flex flex-col md:flex-row items-center md:items-start justify-center gap-6 md:gap-24 w-full max-w-6xl md:h-90">
        <div className="flex flex-col items-center md:items-start justify-between text-center h-full space-y-4 md:space-y-0">
          <p className="text-lg md:text-2xl text-gray-700 leading-snug">
            Um sistema que gera e avalia <br /> unidades curriculares
          </p>

          <Link to="/unidades-curriculares">
            <Button
              className="py-3 md:py-5 px-6 md:px-21 text-xl md:text-4xl h-auto"
              onClick={() =>
                keycloak.login({
                  redirectUri: `${window.location.origin}/unidades-curriculares`,
                })
              }
            >
              Log In
            </Button>
          </Link>

          <p className="text-sm md:text-lg text-gray-600">
            Ainda não tens conta?{" "}
            <a
              href="#"
              className="text-[#41B5C0] hover:underline"
              onClick={(e) => {
                e.preventDefault();
                keycloak.register({
                  redirectUri: `${window.location.origin}/unidades-curriculares`,
                });
              }}
            >
              Cria uma nova
            </a>
          </p>
        </div>

        <img
          src="/logo.png"
          alt="EduPro logo"
          className="w-44 h-44 md:h-full md:w-auto object-contain"
        />
      </div>
    </div>
  );
}
