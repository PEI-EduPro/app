import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { encodeId } from "@/lib/id-encoder";
import { useGetWaitingRooms } from "@/hooks/use-waiting-rooms";

export default function SalasTab({
  realId,
  ucName,
}: {
  realId: number;
  ucName: string;
}) {
  const { data: waitingRooms } = useGetWaitingRooms({ enabled: true });

  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!waitingRooms) return [];
    const closed = waitingRooms.filter(
      (wr) => wr.subject_id === realId && wr.state === "closed",
    );
    const q = search.toLowerCase();
    if (!q) return closed;
    return closed.filter((wr) => wr.exam_name.toLowerCase().includes(q));
  }, [waitingRooms, realId, search]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 sticky top-10 z-10 bg-background py-2 -mx-4 px-4 md:-mx-6 md:px-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Pesquisar salas..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        {search && (
          <Button
            variant="ghost"
            onClick={() => setSearch("")}
            className="text-muted-foreground shrink-0"
          >
            Limpar
          </Button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pt-2 pb-2">
        {filtered.map((wr) => (
          <Link
            key={wr.waiting_room_id}
            to="/exames-correcao"
            search={{
              ucId: encodeId(realId),
              ucName: ucName,
              wrId: encodeId(wr.waiting_room_id),
              wrName: wr.exam_name,
            }}
          >
            <Card className="group flex flex-row items-center gap-4 px-5 py-4 cursor-pointer border border-[#3263A8]/20 bg-linear-to-r from-[#3263A8]/5 to-[#2E2B50]/5 hover:from-[#3263A8]/15 hover:to-[#2E2B50]/15 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 overflow-hidden">
              <div className="shrink-0 w-1 self-stretch rounded-full bg-linear-to-b from-[#41B5C0] to-[#3263A8]" />
              <div className="flex-1 min-w-0">
                <span className="text-base font-semibold text-[#2E2B50] truncate block">
                  {wr.exam_name}
                </span>
                <span className="text-xs text-muted-foreground">Fechada</span>
              </div>
            </Card>
          </Link>
        ))}
        {filtered.length === 0 && (
          <p className="text-center text-muted-foreground py-8">
            Nenhuma sala fechada encontrada.
          </p>
        )}
      </div>
    </div>
  );
}
