import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { ExamConfigCard } from "@/components/exam-config-card";
import { Card } from "@/components/ui/card";
import { useGetExamConfig } from "@/hooks/use-exams";
import { useGetUcById } from "@/hooks/use-ucs";
import type { ExamConfigI } from "@/lib/types";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Pencil, Plus, Trash2, Download, type LucideIcon } from "lucide-react";
import { useCallback, useState } from "react";
import { z } from "zod";

const examesUCSearchSchema = z.object({
  ucId: z.number(),
  ucName: z.string(),
});

export const Route = createFileRoute("/_layout/exames-uc")({
  validateSearch: examesUCSearchSchema,
  component: RouteComponent,
});

const IconButton = ({
  Icon,
  label,
  onClick,
}: {
  Icon: LucideIcon;
  label: string;
  onClick: () => void;
}) => (
  <button
    onClick={(e) => {
      e.stopPropagation();
      onClick();
    }}
    aria-label={label}
    className="p-3 m-1 rounded-full text-gray-700 hover:bg-gray-200 transition-colors duration-150"
  >
    <Icon className="h-6 w-6" />
  </button>
);

const ContentActionCard = ({
  id,
  name,
  ucId,
  ucName,
  examConfig,
}: {
  id: number;
  name: string;
  ucId: number;
  ucName: string;
  examConfig: ExamConfigI;
}) => {
  const navigate = Route.useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = useCallback(() => setIsModalOpen(true), []);
  const handleCloseModal = useCallback(() => setIsModalOpen(false), []);

  const handleUpload = () => console.log("Action: Upload/Move clicked");
  const handleDelete = () => console.log("Action: Delete clicked");

  return (
    <>
      <Card
        className="w-[150px] h-[250px]  group relative cursor-pointer hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]"
        onClick={handleOpenModal}
      >
        <div className="absolute inset-0 bg-[#2E2B50] rounded-[14px] text-white p-4 transition-opacity duration-300 group-hover:opacity-0 z-10 flex items-end">
          <span className="text-xl font-semibold">{name}</span>
        </div>
        <div className="absolute inset-0 bg-gray-100 text-gray-700 p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100 flex flex-col items-center justify-between z-20">
          <div className="flex justify-center w-full">
            <IconButton
              Icon={Download}
              label="Download file"
              onClick={handleUpload}
            />
          </div>
          <div className="flex-grow"></div>
          <div className="flex justify-around w-full">
            <IconButton
              Icon={Pencil}
              label="Edit document"
              onClick={() =>
                navigate({
                  to: "/novo-exame",
                  search: { examId: id, ucId: ucId, ucName: ucName },
                })
              }
            />
            <IconButton
              Icon={Trash2}
              label="Delete document"
              onClick={handleDelete}
            />
          </div>
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
  const { data: ucData } = useGetUcById(ucId);
  const { data: examConfigs } = useGetExamConfig(ucId);

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
      <div className="flex flex-col gap-[10px] items-center justify-center mb-35">
        <span className="font-rubik text-5xl">{ucData?.name}</span>
        <span className="font-rubik text-4xl text-[#2E2B50]">Exames</span>
      </div>
      <div className="px-47.5 grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-x-[70px] gap-y-[50px]">
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
          <Card className="w-[150px] h-[250px] flex-row justify-center items-center bg-[rgba(139,145,160,0.5)] hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]">
            <Plus className="stroke-[rgb(86,89,98)] h-[40px] w-[40px]" />
          </Card>
        </Link>
      </div>
    </div>
  );
}
