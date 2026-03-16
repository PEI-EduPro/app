import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { ExamConfigCard } from "@/components/exam-config-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useGetExamConfig } from "@/hooks/use-exams";
import { useGetUcById } from "@/hooks/use-ucs";
import { decodeId } from "@/lib/id-encoder";
import type { ExamConfigI } from "@/lib/types";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus, Trash2 } from "lucide-react";
import { useCallback, useState } from "react";
import { z } from "zod";

const examesUCSearchSchema = z.object({
  ucId: z.string(),
  ucName: z.string(),
});

export const Route = createFileRoute("/_layout/exames-uc")({
  validateSearch: examesUCSearchSchema,
  component: RouteComponent,
  beforeLoad: ({ search }) => ({
    ucId: decodeId(search.ucId),
  }),
});

const ContentActionCard = ({
  name,
  examConfig,
}: {
  id: number;
  name: string;
  ucId: string;
  ucName: string;
  examConfig: ExamConfigI;
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = useCallback(() => setIsModalOpen(true), []);
  const handleCloseModal = useCallback(() => setIsModalOpen(false), []);

  const handleDelete = () => console.log("Action: Delete clicked");

  return (
    <>
      <Card
        className="w-37.5 h-62.5  group relative hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]"
        onClick={handleOpenModal}
      >
        <div className="absolute inset-0 bg-[#2E2B50] rounded-[14px] text-white p-4 transition-opacity duration-300 group-hover:opacity-0 z-10 flex items-end">
          <span className="text-xl font-semibold">{name}</span>
        </div>
        <div className="absolute inset-0 bg-gray-100 text-gray-700 p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100 flex flex-col items-center justify-center z-20">
          <Button
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation();
              handleDelete();
            }}
            className="cursor-pointer rounded-full p-2 hover:text-red-500 transition-colors duration-150"
          >
            <Trash2 className="h-6.25! w-6.25!" />
          </Button>
        </div>
      </Card>
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={handleCloseModal}
        >
          <div
            className="bg-white rounded-xl shadow-2xl max-w-lg w-full m-4 max-h-[90vh] overflow-y-auto transform transition-all"
            onClick={(e) => e.stopPropagation()}
          >
            <ExamConfigCard examConfigData={examConfig} />
          </div>
        </div>
      )}
    </>
  );
};

function RouteComponent() {
  const { ucId, ucName } = Route.useSearch();
  const realId = decodeId(ucId);

  const { data: ucData } = useGetUcById(realId);
  const { data: examConfigs } = useGetExamConfig(realId);

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page="Exames"
        crumbs={[
          {
            name: "Unidades Curriculares",
            link: "/unidades-curriculares",
          },
          {
            name: ucName,
            link: `/detalhes-uc?ucId=${ucId}`,
          },
        ]}
      />
      <div className="flex flex-col gap-2.5 items-center justify-center mb-35">
        <span className="font-rubik text-5xl">{ucData?.name}</span>
        <span className="font-rubik text-4xl text-[#2E2B50]">Exames</span>
      </div>
      <div className="px-47.5 grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-x-17.5 gap-y-12.5">
        {examConfigs?.map((el, index) => (
          <ContentActionCard
            id={el.id}
            name={`Exame ${index + 1}`}
            ucId={ucId}
            ucName={ucName}
            key={index}
            examConfig={el}
          />
        ))}
        <Link to="/novo-exame" search={{ ucId: ucId, ucName: ucName }}>
          <Card className="w-37.5 h-62.5 flex-row justify-center items-center bg-[rgba(139,145,160,0.5)] hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]">
            <Plus className="stroke-[rgb(86,89,98)] h-10 w-10" />
          </Card>
        </Link>
      </div>
    </div>
  );
}
