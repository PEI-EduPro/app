import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import {
  type NewExamConfigI,
  type ExamConfigI,
  type PostEmailI,
} from "@/lib/types";
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
    mutationFn: (props: NewExamConfigI) =>
      apiClient.post<ExamConfigI>("/exams/generate_async/", props),

    onSuccess: () => {
      toast.dismiss();
      toast.success("Exame criado com sucesso!", {
        position: "top-right",
        duration: 3000,
      });
      queryClient.invalidateQueries({ queryKey: ["examConfig"] });
    },

    onError: () => {
      toast.dismiss();
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
        duration: 3000,
      });
    },
  });
};

const useDownloadExamConfig = () =>
  useMutation({
    mutationFn: (id: number) =>
      apiClient.download(`/exams/config/${id}/download`),

    onSuccess: (blob: Blob) => {
      saveFile(blob, "generated_exam.zip");
    },

    onError: () => {
      toast.error("Erro ao descarregar o exame.", {
        position: "top-right",
        duration: 3000,
      });
    },
  });

const useGetExamConfig = (ucId: number) =>
  useQuery<ExamConfigI[]>({
    queryKey: ["examConfig", ucId],
    queryFn: () => apiClient.get(`/exams/subject/${ucId}/configs`),
    enabled: !!ucId,
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasActive = data?.some(
        (c) => c.status === "PENDING" || c.status === "PROCESSING",
      );
      return hasActive ? 3000 : false;
    },
  });

const useDeleteExamConfig = (ucId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/exams/config/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["examConfig", ucId] });
      toast.success("Configuração de exame eliminada com sucesso!", {
        position: "top-right",
      });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const usePostGrades = (wrId: number) =>
  useMutation({
    mutationFn: (options: PostEmailI) =>
      apiClient.post(`/exams/waiting_room/${wrId}/post_grades`, { options }),
    onSuccess: () => {
      toast.success("Notas lançadas com sucesso!", {
        position: "top-right",
        duration: 3000,
      });
    },
    onError: () => {
      toast.error("Ocorreu um erro ao lançar as notas.", {
        position: "top-right",
        duration: 3000,
      });
    },
  });

export {
  useAddExamConfig,
  useDownloadExamConfig,
  useGetExamConfig,
  useDeleteExamConfig,
  usePostGrades,
};
