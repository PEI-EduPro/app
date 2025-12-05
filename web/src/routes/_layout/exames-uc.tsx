import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { ExamConfigCard } from "@/components/exam-config-card";
import type { NovoExameFormT } from "@/components/novo-exame-form";
import { Card } from "@/components/ui/card";
import { useGetUcById } from "@/hooks/use-ucs";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Pencil, Plus, Trash2, Download, type LucideIcon } from "lucide-react";
import { useCallback, useState } from "react";
import { z } from "zod";

const examConfgExample: NovoExameFormT = {
  topics: [
    { id: "1", nome: "Arquiteturas" },
    { id: "2", nome: "Definição de requisitos avançada" },
    { id: "3", nome: "Introdução à tomada de decisão" },
  ],
  number_questions: {
    "1": 5,
    "2": 3,
    "3": 2,
  },
  relative_quotations: {
    "1": 50,
    "2": 30,
    "3": 20,
  },
  number_exams: 1,
  fraction: 0,
};

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
}: {
  id: number;
  name: string;
  ucId: number;
  ucName: string;
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
            <ExamConfigCard examConfigData={examConfgExample} />
          </div>
        </div>
      )}
    </>
  );
};

function RouteComponent() {
  const { ucId, ucName } = Route.useSearch();
  const { data: ucData } = useGetUcById(ucId);

  const exames = [
    {
      date: "2024-07-15",
      nome: "Exame Normal",
      id: 1,
    },
    {
      date: "2024-07-15",
      nome: "Exame Normal",
      id: 2,
    },
    {
      date: "2024-07-15",
      nome: "Exame Normal",
      id: 3,
    },
    {
      date: "2024-07-15",
      nome: "Exame Normal",
      id: 4,
    },
    {
      date: "2024-07-15",
      nome: "Exame Normal",
      id: 5,
    },
    {
      date: "2024-07-15",
      nome: "Exame Normal",
      id: 6,
    },
  ];

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
        {exames.map((el, index) => (
          <ContentActionCard
            id={el.id}
            name={el.nome}
            ucId={ucId}
            ucName={ucName}
            key={index}
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
