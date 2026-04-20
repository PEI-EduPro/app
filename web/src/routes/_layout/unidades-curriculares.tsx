import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useKeycloak } from "@/hooks/use-keycloak";
import { useIsMobile } from "@/hooks/use-mobile";
import { useGetUc, useDeleteUcById, useGetUcProfessors, useGetUcRegent, useUpdateUc } from "@/hooks/use-ucs";
import { useGetProfessors } from "@/hooks/use-users";
import { encodeId } from "@/lib/id-encoder";
import type { UserI, WaitingRoomStatusT } from "@/lib/types";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { LoaderCircle, Plus, Search, Trash2, X } from "lucide-react";
import { useState } from "react";
import { useGetWaitingRooms } from "@/hooks/use-waiting-rooms";

export const Route = createFileRoute("/_layout/unidades-curriculares")({
  component: UCS,
});

const formatUserName = (user: UserI) =>
  user?.first_name && user?.last_name
    ? `${user.first_name} ${user.last_name}`
    : user?.firstName && user?.lastName
      ? `${user.firstName} ${user.lastName}`
      : user?.username || "";

function EditUcForm({
  ucId,
  ucName,
  initialProfs,
  initialRegent,
  allProfessors,
  onClose,
}: {
  ucId: number;
  ucName: string;
  initialProfs: { id: string; nome: string; email: string }[];
  initialRegent: { id: string; nome: string; email: string } | undefined;
  allProfessors: { id: string; nome: string; email: string }[];
  onClose: () => void;
}) {
  const { mutate: updateUc } = useUpdateUc(ucId);
  const [profsSelection, setProfsSelection] = useState(initialProfs);
  const [regentSelection, setRegentSelection] = useState(initialRegent);

  function handleSave() {
    if (regentSelection) {
      updateUc({ regent_keycloak_id: regentSelection.id, professor_keycloak_ids: profsSelection.map((p) => p.id) });
    }
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-background rounded-xl shadow-2xl w-full max-w-3xl m-4 max-h-[90vh] overflow-y-auto p-8 flex flex-col gap-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <span className="font-rubik text-2xl font-bold">{ucName}</span>
          <Button variant="ghost" size="icon" className="cursor-pointer" onClick={onClose}><X /></Button>
        </div>
        <div className="flex flex-row gap-8">
          <div className="flex-1 flex flex-col gap-2">
            <span className="text-lg font-medium">Regente</span>
            <Select value={regentSelection?.id} onValueChange={(e) => {
              const option = allProfessors.find((p) => p.id === e);
              if (option) setRegentSelection(option);
            }}>
              <SelectTrigger className="shadow-none w-full"><SelectValue placeholder="Selecione um docente" /></SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {allProfessors.map((p) => <SelectItem key={p.id} value={p.id}>{p.nome}</SelectItem>)}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1 flex flex-col gap-2">
            <span className="text-lg font-medium">Professores</span>
            <CustomTable
              data={allProfessors.filter((p) => p.id !== regentSelection?.id)}
              isSelectable
              rowSelection={profsSelection}
              rowNumber={5}
              onChange={(e) => setProfsSelection(e as { id: string; nome: string; email: string }[])}
            />
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" className="cursor-pointer" onClick={onClose}>Cancelar</Button>
          <Button className="cursor-pointer" onClick={handleSave}>Guardar</Button>
        </div>
      </div>
    </div>
  );
}

function EditUcModal({ ucId, ucName, onClose }: { ucId: number; ucName: string; onClose: () => void }) {
  const { data: professors = [], isLoading: loadingProfs } = useGetUcProfessors(ucId);
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(ucId);
  const { data: allProfessors = [] } = useGetProfessors();

  const allProfessorsData = allProfessors.map((p) => ({ id: p.id, nome: formatUserName(p), email: p.email || "" }));

  if (loadingProfs || loadingRegent) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
        <LoaderCircle className="animate-spin size-16 text-primary" />
      </div>
    );
  }

  const initialProfs = professors.map((p) => ({ id: p.id, nome: formatUserName(p), email: p.email || "" }));
  const initialRegent = regent ? { id: regent.id, nome: formatUserName(regent), email: regent.email || "" } : undefined;

  return (
    <EditUcForm
      key={`${ucId}-${regent?.id}-${professors.map(p => p.id).join(',')}`}
      ucId={ucId}
      ucName={ucName}
      initialProfs={initialProfs}
      initialRegent={initialRegent}
      allProfessors={allProfessorsData}
      onClose={onClose}
    />
  );
}


interface UCCardProps {
  srcImage?: string;
  label: string;
  id: number;
  waitingRoomStatus?: WaitingRoomStatusT;
  index?: number;
  selectionMode?: boolean;
  onSelect?: (id: number) => void;
  onEdit?: (id: number, name: string) => void;
}

function UCCard({
  label,
  srcImage,
  id,
  waitingRoomStatus,
  index = 0,
  selectionMode = false,
  onSelect,
  onEdit,
}: UCCardProps) {
  const isMobile = useIsMobile();

  if (selectionMode) {
    return (
      <div
        onClick={() => onSelect?.(id)}
        className="w-full md:w-fit animate-fade-in-up h-fit cursor-pointer"
        style={{ animationDelay: `${index * 0.07}s` }}
      >
        <Card className="w-full md:w-80 md:h-57.5 py-0 overflow-hidden gap-2.5 border-2 border-destructive/40 bg-destructive/5 hover:bg-destructive/10 hover:border-destructive hover:-translate-y-1 active:translate-y-0 shadow-md hover:shadow-xl group">
          <div className="relative overflow-hidden">
            <img
              src={srcImage || "/card-image.png"}
              className="hidden md:block w-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          </div>
          <span className="hidden md:block px-3 pb-3 font-medium text-foreground line-clamp-2">
            {label}
          </span>
          <div className="flex md:hidden items-center gap-3 p-2">
            <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0">
              <img src={srcImage || "/card-image.png"} className="w-full h-full object-cover" />
            </div>
            <span className="text-sm font-medium leading-snug line-clamp-2 text-foreground">{label}</span>
          </div>
        </Card>
      </div>
    );
  }

  if (onEdit) {
    return (
      <div
        onClick={() => onEdit(id, label)}
        className="w-full md:w-fit animate-fade-in-up h-fit cursor-pointer"
        style={{ animationDelay: `${index * 0.07}s` }}
      >
        <Card className="w-full md:w-80 md:h-57.5 py-0 overflow-hidden gap-2.5 border-0 shadow-md hover:shadow-xl hover:-translate-y-1 active:translate-y-0 active:shadow-md cursor-pointer group">
          <div className="relative overflow-hidden">
            <img src={srcImage || "/card-image.png"} className="hidden md:block w-full object-cover group-hover:scale-105 transition-transform duration-500" />
            <div className="hidden md:block absolute inset-0 bg-linear-to-t from-[#2E2B50]/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
          <span className="hidden md:block px-3 pb-3 font-medium text-foreground line-clamp-2">{label}</span>
          <div className="flex md:hidden items-center gap-3 p-2">
            <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0">
              <img src={srcImage || "/card-image.png"} className="w-full h-full object-cover" />
            </div>
            <span className="text-sm font-medium leading-snug line-clamp-2 text-foreground">{label}</span>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <Link
      to={
        isMobile
          ? waitingRoomStatus !== "closed"
            ? "/mobile_scan_teste"
            : `/mobile_evaluate_tests`
          : `/detalhes-uc`
      }
      search={{ ucId: encodeId(id) }}
      className="w-full md:w-fit animate-fade-in-up h-fit"
      style={{ animationDelay: `${index * 0.07}s` }}
    >
      <Card className="w-full md:w-80 md:h-57.5 py-0 overflow-hidden gap-2.5 border-0 shadow-md hover:shadow-xl hover:-translate-y-1 active:translate-y-0 active:shadow-md cursor-pointer group">
        <div className="relative overflow-hidden">
          <img
            src={srcImage || "/card-image.png"}
            className="hidden md:block w-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="hidden md:block absolute inset-0 bg-linear-to-t from-[#2E2B50]/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>

        <div className="flex md:hidden items-center gap-3 p-2">
          <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0">
            <img
              src={srcImage || "/card-image.png"}
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex flex-col gap-1 min-w-0">
            <span className="text-sm font-medium leading-snug line-clamp-2 text-foreground">
              {label}
            </span>
            {waitingRoomStatus && (
              <span
                className={`text-xs font-semibold w-fit px-2 py-0.5 rounded-full ${
                  waitingRoomStatus === "running"
                    ? "bg-green-100 text-green-700"
                    : waitingRoomStatus === "preparation"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-gray-100 text-gray-500"
                }`}
              >
                {waitingRoomStatus === "running"
                  ? "A decorrer"
                  : waitingRoomStatus === "preparation"
                    ? "Em preparação"
                    : "Fechado"}
              </span>
            )}
          </div>
        </div>

        <span className="hidden md:block px-3 pb-3 font-medium text-foreground line-clamp-2">
          {label}
        </span>
      </Card>
    </Link>
  );
}

function UCS() {
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const { data, isLoading } = useGetUc({ enabled: !isMobile });
  const { data: waitingRooms = [], isLoading: waitingRoomsLoading } =
    useGetWaitingRooms({ enabled: isMobile });
  const { keycloak } = useKeycloak();
  const isManager =
    (keycloak.tokenParsed?.realm_access?.roles || []).find(
      (e) => e == "manager",
    ) != undefined;
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState<WaitingRoomStatusT | "all">(
    "all",
  );
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedUcId, setSelectedUcId] = useState<number | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [editUc, setEditUc] = useState<{ id: number; name: string } | null>(null);

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
        <AppBreadcrumb page="Unidades Curriculares" />
        <div className="font-rubik flex justify-center text-lg md:text-5xl mb-7 md:mb-8 font-bold text-foreground animate-fade-in-up">
          Unidades Curriculares
        </div>
        <div className="flex items-center gap-2 w-full md:px-47.5 mx-auto mb-4 md:mb-12 animate-fade-in-up">
          {isManager && !isMobile && (
            <div className="flex gap-2 shrink-0">
              <Button
                size="sm"
                onClick={() => navigate({ to: "/nova-uc" })}
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
          <div className="flex gap-2 mb-6 overflow-x-auto pb-1 animate-fade-in-up">
            {(["all", "running", "preparation", "closed"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStateFilter(s)}
                className={`shrink-0 text-xs font-semibold px-3 py-1 rounded-full border transition-colors ${
                  stateFilter === s
                    ? s === "running"
                      ? "bg-green-600 text-white border-green-600"
                      : s === "preparation"
                        ? "bg-yellow-500 text-white border-yellow-500"
                        : s === "closed"
                          ? "bg-gray-500 text-white border-gray-500"
                          : "bg-primary text-primary-foreground border-primary"
                    : "bg-transparent text-muted-foreground border-border"
                }`}
              >
                {s === "all"
                  ? "Todos"
                  : s === "running"
                    ? "A decorrer"
                    : s === "preparation"
                      ? "Em preparação"
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
                    srcImage={"/card-image.png"}
                    id={el.waiting_room_id}
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
                    srcImage={"/card-image.png"}
                    id={el.id}
                    key={index}
                    index={index}
                    selectionMode={selectionMode}
                    onSelect={handleUcSelect}
                    onEdit={isManager && !selectionMode ? (id, name) => setEditUc({ id, name }) : undefined}
                  />
                ))
              ))}
        </div>
      )}

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
              <Trash2 />
            </AlertDialogMedia>
            <AlertDialogTitle className="font-medium text-2xl">Eliminar Unidade Curricular</AlertDialogTitle>
            <AlertDialogDescription className="font-medium text-xl">
              Esta ação irá eliminar permanentemente esta unidade curricular. Deseja continuar?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="w-full! flex flex-row justify-between!">
            <AlertDialogCancel variant="outline" size="lg" className="cursor-pointer text-xl" onClick={() => { setSelectionMode(false); setSelectedUcId(null); }}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction size="lg" variant="destructive" className="cursor-pointer text-xl" onClick={handleConfirmDelete}>
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {editUc && (
        <EditUcModal ucId={editUc.id} ucName={editUc.name} onClose={() => setEditUc(null)} />
      )}
    </div>
  );
}
