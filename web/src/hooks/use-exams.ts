import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import { type NewExamConfigI, type ExamConfigI } from "@/lib/types";
import { toast } from "sonner";

const saveFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url;
  a.download = filename;

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  window.URL.revokeObjectURL(url);
};

const useAddExamConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["createExam", "download"],
    mutationFn: (props: NewExamConfigI) =>
      apiClient.download("/exams/generate/", props),

    onSuccess: (zipBlob: Blob) => {
      saveFile(zipBlob, "generated_exam.zip");

      queryClient.invalidateQueries({ queryKey: ["examConfig"] });
    },
  });
};

const useGetExamConfig = (ucId: number) =>
  useQuery<ExamConfigI[]>({
    queryKey: ["examConfig", ucId],
    queryFn: () => apiClient.get(`/exams/subject/${ucId}/configs`),
    enabled: !!ucId,
  });

const useDeleteExamConfig = (ucId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/exams/config/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["examConfig", ucId] });
      toast.success("Configuração de exame eliminada com sucesso", {
        position: "top-right",
      });
    },
    onError: () => {
      toast.error("ocorreu um erro, tente novamente mais tarde", {
        position: "top-right",
      });
    },
  });
};

export { useAddExamConfig, useGetExamConfig, useDeleteExamConfig };
