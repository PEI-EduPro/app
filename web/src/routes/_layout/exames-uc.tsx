import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { ExamConfigCard } from "@/components/exam-config-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useGetExamConfig } from "@/hooks/use-exams";
import { useGetUcById } from "@/hooks/use-ucs";
import { decodeId } from "@/lib/id-encoder";
import type { ExamConfigI } from "@/lib/types";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus, Trash2Icon } from "lucide-react";
import { useCallback, useState } from "react";
import { z } from "zod";
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
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

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
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                }}
                className="cursor-pointer rounded-full p-2 hover:text-red-500 transition-colors duration-150"
              >
                <Trash2Icon className="h-6.25! w-6.25!" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                  <Trash2Icon />
                </AlertDialogMedia>
                <AlertDialogTitle className="font-medium text-2xl">
                  Apagar Configuração de Exame
                </AlertDialogTitle>
                <AlertDialogDescription className="font-medium text-xl">
                  {` Esta ação irá apagar permanentemente a configuração de exame. Deseja continuar?`}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                <AlertDialogCancel
                  variant="outline"
                  className="cursor-pointer text-xl"
                  size="lg"
                >
                  Cancelar
                </AlertDialogCancel>
                <AlertDialogAction
                  size="lg"
                  variant="destructive"
                  className="cursor-pointer text-xl"
                  onClick={() => handleDelete()}
                >
                  Apagar
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
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
    <div className="flex flex-col h-screen overflow-hidden py-3.5 px-6 w-full">
      <div className="shrink-0">
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
        <div className="flex flex-col gap-2.5 items-center justify-center mb-25">
          <span className="font-rubik text-5xl">{ucData?.name}</span>
          <span className="font-rubik text-4xl text-[#2E2B50]">Exames</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-47.5 grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-x-17.5 gap-y-12.5">
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
          <Card className="w-37.5 h-62.5 flex-col justify-center items-center gap-0 bg-[rgba(139,145,160,0.5)] hover:shadow-[4px_4px_4px_0px_rgba(174,174,174,0.25)]">
            <Plus className="stroke-[rgb(86,89,98)] h-10 w-10" />
            <span className="text-xl font-medium text-[rgb(86,89,98)]">
              Criar Exame
            </span>
          </Card>
        </Link>
      </div>
    </div>
  );
}
