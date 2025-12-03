import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { NovoExameForm } from "@/components/novo-exame-form";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout/novo-exame")({
  component: NovoExame,
});

function NovoExame() {
  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page="Novo Exame"
        crumbs={[
          {
            name: "Unidades Curriculares",
            link: "/unidades-curriculares",
          },
          {
            name: "NOME_UC",  // hardcoded name
            link: "/",   // hardcoded id
          },
        ]}
      />
      <div className="flex justify-center text-5xl mb-35">
        Novo Exame
      </div>
      <div className="flex flex-col items-center">
        <div className="w-[700px] h-auto">
          <NovoExameForm />
        </div>
      </div>
    </div>
  );
}
