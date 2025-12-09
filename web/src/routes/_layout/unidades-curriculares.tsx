import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { Card } from "@/components/ui/card";
import { useGetUc } from "@/hooks/use-ucs";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";

export const Route = createFileRoute("/_layout/unidades-curriculares")({
  component: UCS,
});

interface UCCArdProps {
  srcImage?: string;
  label: string;
  id: number;
}
function UCCard({ label, srcImage, id }: UCCArdProps) {
  return (
    <Link to={`/detalhes-uc`} search={{ ucId: id }}>
      <Card className="w-80 h-57.5 py-0 overflow-hidden gap-2.5 hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]">
        <img src={srcImage || "/card-image.png"} />
        <span className="px-1.75 h-auto line-clamp-2 overflow-hidden text-ellipsis">
          {label}
        </span>
      </Card>
    </Link>
  );
}

function UCS() {
  const { data } = useGetUc();

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb page="Unidades Curriculares" />
      <div className="font-rubik flex justify-center text-5xl mb-35">
        Unidades Curriculares
      </div>
      <div className="px-47.5 grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-x-[70px] gap-y-[50px]">
        {data?.map((el, index) => (
          <UCCard
            label={el.name}
            srcImage={"/card-image.png"}
            id={el.id}
            key={index}
          />
        ))}
        <Link to="/nova-uc">
          <Card className="w-80 h-57.5 flex-row justify-center items-center bg-[rgba(139,145,160,0.5)] hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]">
            <Plus className="stroke-[rgb(86,89,98)] h-[40px] w-[40px]" />
          </Card>
        </Link>
      </div>
    </div>
  );
}
