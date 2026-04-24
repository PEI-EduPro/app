import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { Button } from "@/components/ui/button";
import UcTabs from "@/components/uc-tabs/uc-tabs";
import {
  useGetUcById,
  useGetUcProfessors,
  useGetUcRegent,
} from "@/hooks/use-ucs";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";
import { decodeId } from "@/lib/id-encoder";
import { useKeycloak } from "@/hooks/use-keycloak";
import { LoaderCircle, Pencil } from "lucide-react";
import { NovaUcModal } from "@/components/nova-uc-modal";

const detalheUCSearchSchema = z.object({
  ucId: z.string(),
});

export const Route = createFileRoute("/_layout/detalhes-uc")({
  validateSearch: detalheUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

function PersonCard({ name, email }: { name: string; email: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 rounded-md bg-muted/50">
      <span className="font-medium text-sm">{name}</span>
      {email && (
        <>
          <span className="text-muted-foreground text-sm">·</span>
          <span className="text-sm text-muted-foreground">{email}</span>
        </>
      )}
    </div>
  );
}

function RouteComponent() {
  const { ucId } = Route.useSearch();
  const realId = decodeId(ucId);
  const { keycloak } = useKeycloak();
  const currentUserId = keycloak.tokenParsed?.sub as string | undefined;

  const { data: ucData } = useGetUcById(realId);
  const { data: professors = [], isLoading: loadingProfs } =
    useGetUcProfessors(realId);
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(realId);

  const [editingProfessors, setEditingProfessors] = useState(false);

  const isRegent = !!currentUserId && regent?.id === currentUserId;

  const formatUserName = (u: {
    first_name?: string;
    last_name?: string;
    firstName?: string;
    lastName?: string;
    username?: string;
  }) =>
    u.first_name && u.last_name
      ? `${u.first_name} ${u.last_name}`
      : u.firstName && u.lastName
        ? `${u.firstName} ${u.lastName}`
        : u.username || "";

  return (
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-4 md:px-6 w-full">
      <AppBreadcrumb
        page={ucData?.name || "Detalhes"}
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
        ]}
      />
      <div className="overflow-y-auto overflow-x-hidden scrollbar-hide flex-1">
        <div className="w-full md:px-47.5 min-w-max">
          <div className="flex flex-row mb-8 items-center gap-4">
            <span className="font-rubik typography-h1 flex-1 text-center min-w-0 wrap-break-word">
              {ucData?.name || "Carregando..."}
            </span>
          </div>

          <div className="flex flex-col gap-10">
            {loadingProfs || loadingRegent ? (
              <div className="flex justify-center items-center w-full h-40">
                <LoaderCircle className="animate-spin size-16" />
              </div>
            ) : (
              <div className="border rounded-xl p-5 flex flex-col gap-4 relative">
                {isRegent && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="max-w-21 top-4 left-4 gap-1 cursor-pointer mb-4"
                    onClick={() => setEditingProfessors(true)}
                  >
                    <Pencil className="h-3.5 w-3.5" />
                    Editar
                  </Button>
                )}

                <div className="flex flex-col gap-2">
                  <span className="typography-h4">Regente</span>
                  {regent ? (
                    <PersonCard
                      name={formatUserName(regent)}
                      email={regent.email || ""}
                    />
                  ) : (
                    <span className="text-muted-foreground text-sm">
                      Sem regente.
                    </span>
                  )}
                </div>

                <div className="flex flex-col gap-2">
                  <span className="typography-h4">Professores</span>
                  {professors.length === 0 ? (
                    <span className="text-muted-foreground text-sm">
                      Sem professores.
                    </span>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {professors.map((p) => (
                        <PersonCard
                          key={p.id}
                          name={formatUserName(p)}
                          email={p.email || ""}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {editingProfessors && (
              <NovaUcModal
                ucId={realId}
                ucName={ucData?.name}
                lockRegente
                onClose={() => setEditingProfessors(false)}
              />
            )}

            <UcTabs realId={realId} ucId={ucId} ucName={ucData?.name || ""} />
          </div>
          <div></div>
        </div>
      </div>
    </div>
  );
}
