import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { DeleteUcDialog } from "@/components/nova-uc/delete-uc-dialog";
import { NovaUcModal } from "@/components/nova-uc/nova-uc-modal";
import { UCCard } from "@/components/nova-uc/uc-card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useKeycloak } from "@/hooks/use-keycloak";
import { useIsMobile } from "@/hooks/use-mobile";
import { useGetUc, useDeleteUcById } from "@/hooks/use-ucs";
import type { ExamWorkflowStatus } from "@/lib/types";
import { createFileRoute } from "@tanstack/react-router";
import { LoaderCircle, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { useGetExamSessions } from "@/hooks/use-exams";

export const Route = createFileRoute("/_layout/unidades-curriculares")({
  component: UCS,
});

function UCS() {
  const isMobile = useIsMobile();
  const { data, isLoading } = useGetUc({ enabled: !isMobile });
  const { data: waitingRooms = [], isLoading: waitingRoomsLoading } =
    useGetExamSessions({ enabled: isMobile });
  const { keycloak } = useKeycloak();
  const isManager =
    (keycloak.tokenParsed?.realm_access?.roles || []).find(
      (e) => e == "manager",
    ) != undefined;
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState<ExamWorkflowStatus | "all">(
    "all",
  );
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedUcId, setSelectedUcId] = useState<number | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [editUc, setEditUc] = useState<{ id: number; name: string } | null>(
    null,
  );
  const [novaUcOpen, setNovaUcOpen] = useState(false);

  const { mutate: deleteUc } = useDeleteUcById(selectedUcId ?? 0);

  const filteredData = data?.filter((el) =>
    el.name.toLowerCase().includes(search.toLowerCase()),
  );

  const filteredWaitingRooms = waitingRooms.filter((el) => {
    const matchesSearch = `${el.subject_name} - ${el.exam_name}`
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesState = stateFilter === "all" || el.state === stateFilter;
    return matchesSearch && matchesState;
  });

  function handleUcSelect(id: number) {
    setSelectedUcId(id);
    setConfirmOpen(true);
  }

  function handleConfirmDelete() {
    if (selectedUcId !== null) {
      deleteUc(selectedUcId);
    }
    setSelectionMode(false);
    setSelectedUcId(null);
    setConfirmOpen(false);
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-4 md:px-6 w-full">
      <div className="shrink-0">
        <AppBreadcrumb page={isMobile ? "Exames" : "Unidades Curriculares"} />

        <div className="font-rubik flex justify-center mb-7 md:mb-8 font-bold text-foreground animate-fade-in-up typography-h1">
          {isMobile ? "Exames" : "Unidades Curriculares"}
        </div>
        <div className="flex items-center gap-2 w-full md:px-47.5 mx-auto mb-4 md:mb-12 animate-fade-in-up">
          {isManager && !isMobile && (
            <div className="flex gap-2 shrink-0">
              <Button
                size="sm"
                onClick={() => setNovaUcOpen(true)}
                className="gap-1 cursor-pointer"
              >
                <Plus className="h-4 w-4" />
                Nova UC
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => setSelectionMode((v) => !v)}
                className="gap-1 cursor-pointer"
              >
                <Trash2 className="h-4 w-4" />
                {selectionMode ? "Cancelar" : "Eliminar UC"}
              </Button>
            </div>
          )}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Pesquisar..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
        {isMobile && (
          <div className="flex gap-2 mb-4 animate-fade-in-up">
            {(
              ["all", "running", "preparing", "closed_and_capture"] as const
            ).map((s) => (
              <button
                key={s}
                onClick={() => setStateFilter(s)}
                className={`text-xs font-semibold px-3 py-1 rounded-full border transition-colors ${
                  stateFilter === s
                    ? s === "running"
                      ? "bg-green-600 text-white border-green-600"
                      : s === "preparing"
                        ? "bg-yellow-500 text-white border-yellow-500"
                        : s === "closed_and_capture"
                          ? "bg-gray-500 text-white border-gray-500"
                          : "bg-primary text-primary-foreground border-primary"
                    : "bg-transparent text-muted-foreground border-border"
                }`}
              >
                {s === "all"
                  ? "Todos"
                  : s === "running"
                    ? "Decorrer"
                    : s === "preparing"
                      ? "Preparação"
                      : "Fechado"}
              </button>
            ))}
          </div>
        )}
      </div>

      {isLoading || waitingRoomsLoading ? (
        <div className="flex justify-center items-center w-full h-40">
          <LoaderCircle className="animate-spin size-16 text-primary" />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto flex flex-col md:px-47.5 md:grid md:grid-cols-[repeat(auto-fill,minmax(320px,1fr))] md:auto-rows-min md:items-start md:gap-x-17.5 gap-y-3 md:gap-y-8 pt-2">
          {isMobile
            ? waitingRooms &&
              (filteredWaitingRooms.length === 0 ? (
                <div className="col-span-full flex flex-col items-center gap-4 animate-fade-in">
                  <span className="text-s text-muted-foreground">
                    Nenhum exame disponivel.
                  </span>
                </div>
              ) : (
                filteredWaitingRooms.map((el, index) => (
                  <UCCard
                    waitingRoomStatus={el.state}
                    label={`${el.subject_name} - ${el.exam_name}`}
                    srcImage={`${import.meta.env.BASE_URL}card-image.png`}
                    id={el.exam_config_id}
                    key={index}
                    index={index}
                  />
                ))
              ))
            : data &&
              (filteredData?.length === 0 ? (
                <div className="col-span-full flex flex-col items-center gap-4 animate-fade-in">
                  <span className="text-2xl text-muted-foreground">
                    Nenhuma unidade curricular encontrada.
                  </span>
                </div>
              ) : (
                filteredData?.map((el, index) => (
                  <UCCard
                    label={el.name}
                    srcImage={`${import.meta.env.BASE_URL}card-image.png`}
                    id={el.id}
                    key={index}
                    index={index}
                    selectionMode={selectionMode}
                    onSelect={handleUcSelect}
                    onEdit={
                      isManager && !selectionMode
                        ? (id, name) => setEditUc({ id, name })
                        : undefined
                    }
                  />
                ))
              ))}
        </div>
      )}

      <DeleteUcDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setSelectionMode(false);
          setSelectedUcId(null);
        }}
      />

      {editUc && (
        <NovaUcModal
          ucId={editUc.id}
          ucName={editUc.name}
          onClose={() => setEditUc(null)}
        />
      )}

      {novaUcOpen && <NovaUcModal onClose={() => setNovaUcOpen(false)} />}
    </div>
  );
}
