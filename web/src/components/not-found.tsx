import { Link } from "@tanstack/react-router";

export function NotFound() {
  return (
    <div className="flex flex-col items-center mt-10 md:mt-42.5 px-4 md:px-0">
      <h1 className="font-rubik text-3xl md:text-5xl font-semibold text-center mb-5 md:mb-20">
        Upsi! Página não encontrada
      </h1>
      <div className="flex flex-row gap-4 items-center">
        <span className="font-semibold text-[300px] leading-normal">4</span>
        <img
          src="/logo-o.png"
          alt="EduPro logo"
          className="w-40 h-40 md:h-75 md:w-auto"
        />
        <span className="font-semibold text-[300px] leading-normal">4</span>
      </div>

      <Link
        to="/unidades-curriculares"
        className="text-[#41B5C0] hover:underline text-1xl md:text-3xl mt-5 mt:mb-20"
      >
        Voltar a pagina principal
      </Link>
    </div>
  );
}
