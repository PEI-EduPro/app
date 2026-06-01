import { Card } from "@/components/ui/card";
import { useIsMobile } from "@/hooks/use-mobile";
import { encodeId } from "@/lib/id-encoder";
import type { ExamWorkflowStatus } from "@/lib/types";
import { Link } from "@tanstack/react-router";

export interface UCCardProps {
  srcImage?: string;
  label: string;
  id: number;
  waitingRoomStatus?: ExamWorkflowStatus;
  index?: number;
  selectionMode?: boolean;
  onSelect?: (id: number) => void;
  onEdit?: (id: number, name: string) => void;
}

export function UCCard({
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
          <div className="hidden md:block relative overflow-hidden">
            <img
              src={srcImage || "/card-image.png"}
              className="w-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          </div>
          <span className="px-3 pb-3 font-medium text-foreground line-clamp-2">
            {label}
          </span>
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
        <Card className="w-full md:w-80 md:h-57.5 py-0 overflow-hidden gap-2.5 border border-border shadow-md hover:shadow-xl hover:-translate-y-1 active:translate-y-0 active:shadow-md cursor-pointer group">
          <div className="hidden md:block relative overflow-hidden">
            <img
              src={srcImage || `${import.meta.env.BASE_URL}card-image.png`}
              className="hidden md:block w-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
            <div className="absolute inset-0 bg-linear-to-t from-[#2E2B50]/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
          <span className="px-3 pb-3 font-medium text-foreground line-clamp-2">
            {label}
          </span>
          <div className="flex md:hidden items-center gap-3 p-2">
            <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0">
              <img
                src={srcImage || `${import.meta.env.BASE_URL}card-image.png`}
                className="w-full h-full object-cover"
              />
            </div>
            <span className="text-sm font-medium leading-snug line-clamp-2 text-foreground">
              {label}
            </span>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <Link
      to={
        isMobile
          ? waitingRoomStatus === "running" || waitingRoomStatus === "preparing"
            ? "/mobile_scan_teste"
            : "/mobile_evaluate_tests"
          : "/detalhes-uc"
      }
      search={{ ucId: encodeId(id) }}
      className="w-full md:w-fit animate-fade-in-up h-fit"
      style={{ animationDelay: `${index * 0.07}s` }}
    >
      <Card className="w-full md:w-80 md:h-57.5 py-0 overflow-hidden gap-2.5 border border-border shadow-md hover:shadow-xl hover:-translate-y-1 active:translate-y-0 active:shadow-md cursor-pointer group">
        <div className="hidden md:block relative overflow-hidden">
          <img
            src={srcImage || `${import.meta.env.BASE_URL}card-image.png`}
            className="hidden md:block w-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="hidden md:block absolute inset-0 bg-linear-to-t from-[#2E2B50]/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>
        <div className="flex md:hidden items-center gap-3 p-2">
          <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0">
            <img
              src={srcImage || `${import.meta.env.BASE_URL}card-image.png`}
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
                    : waitingRoomStatus === "preparing"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-gray-100 text-gray-500"
                }`}
              >
                {waitingRoomStatus === "running"
                  ? "A decorrer"
                  : waitingRoomStatus === "preparing"
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
