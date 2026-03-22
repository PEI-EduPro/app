import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { Card } from "@/components/ui/card";
import { useKeycloak } from "@/hooks/use-keycloak";
import { useIsMobile } from "@/hooks/use-mobile";
import { useGetUc, useGetWaitingRooms } from "@/hooks/use-ucs";
import { encodeId } from "@/lib/id-encoder";
import { createFileRoute, Link } from "@tanstack/react-router";
import { LoaderCircle, Plus } from "lucide-react";

export const Route = createFileRoute("/_layout/unidades-curriculares")({
  component: UCS,
});

interface UCCArdProps {
  srcImage?: string;
  label: string;
  id: number;
}
function UCCard({ label, srcImage, id }: UCCArdProps) {
  const isMobile = useIsMobile();

  return (
    <Link
      to={isMobile ? `/mobile_evaluate_tests` : `/detalhes-uc`}
      search={{ ucId: encodeId(id) }}
      className="w-fit"
    >
      <Card className="w-80 md:h-57.5 py-0 overflow-hidden gap-2.5 hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)] active:shadow-[inset_2px_2px_4px_0px_rgba(174,174,174,0.35)] transition-shadow duration-200">
        <img src={srcImage || "/card-image.png"} className="hidden md:block" />

        <div className="flex md:hidden items-center gap-3">
          <div className="w-12 h-12 rounded-bl-lg rounded-tl-lg overflow-hidden bg-muted">
            <img
              src={srcImage || "/card-image.png"}
              className="w-full h-full object-cover"
            />
          </div>
          <span className="text-sm font-medium leading-snug line-clamp-2 text-foreground">
            {label}
          </span>
        </div>

        <span className="hidden md:block px-1.75 h-auto line-clamp-2 overflow-hidden text-ellipsis">
          {label}
        </span>
      </Card>
    </Link>
  );
}

function UCS() {
  const { data, isLoading } = useGetUc();
  const { data: waitingRooms = [], isLoading: waitingRoomsLoading } =
    useGetWaitingRooms();
  const { keycloak } = useKeycloak();
  const isManager =
    (keycloak.tokenParsed?.realm_access?.roles || []).find(
      (e) => e == "manager",
    ) != undefined;
  const isMobile = useIsMobile();

  return (
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-6 w-full">
      <div className="shrink-0">
        <AppBreadcrumb page="Unidades Curriculares" />
        <div className="font-rubik flex justify-center text-lg md:text-5xl mb-7 md:mb-25">
          Unidades Curriculares
        </div>
      </div>
      {isLoading || waitingRoomsLoading ? (
        <div className="flex justify-center items-center w-full h-40">
          <LoaderCircle className="animate-spin size-16" />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto md:px-47.5 grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] md:gap-x-17.5 gap-y-7 md:gap-y-12.5">
          {isMobile
            ? waitingRooms &&
              (waitingRooms.length === 0 ? (
                <div className="col-span-full flex flex-col items-center gap-4">
                  <span className="text-s text-gray-500">
                    Nenhuma unidade curricular encontrada.
                  </span>
                </div>
              ) : (
                waitingRooms?.map((el, index) => (
                  <UCCard
                    label={el.subject_name}
                    srcImage={"/card-image.png"}
                    id={el.subject_id}
                    key={index}
                  />
                ))
              ))
            : data &&
              (data.length === 0 && !isManager ? (
                <div className="col-span-full flex flex-col items-center gap-4">
                  <span className="text-2xl text-gray-500">
                    Nenhuma unidade curricular encontrada.
                  </span>
                </div>
              ) : (
                data?.map((el, index) => (
                  <UCCard
                    label={el.name}
                    srcImage={"/card-image.png"}
                    id={el.id}
                    key={index}
                  />
                ))
              ))}

          {isManager && !isLoading && !isMobile && (
            <Link to="/nova-uc" className="w-fit">
              <Card className="w-80 h-57.5 flex-row justify-center items-center bg-[rgba(139,145,160,0.5)] hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]">
                <Plus className="stroke-[rgb(86,89,98)] h-10 w-10" />
                <span className="text-xl font-medium text-[rgb(86,89,98)]">
                  Criar Unidade Curricular
                </span>
              </Card>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
