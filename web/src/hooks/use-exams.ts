import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import {
  type NewExamConfigI,
  type ExamConfigI,
  type PostEmailI,
  type ExamCorrectionI,
  type ExamResponseI,
  type GetExamSessionInfoI,
  type GetExamSessionI,
  type GetExamSessionMetricsI,
  type GetWarningsI,
  type PostExamStudentI,
  type PostResolveWarningsI,
  type StudentsI,
  type ExamWorkflowStatus,
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
    onSuccess: (blob: Blob) => saveFile(blob, "generated_exam.zip"),
    onError: () =>
      toast.error("Erro ao descarregar o exame.", {
        position: "top-right",
        duration: 3000,
      }),
  });

const useGetExamConfigById = (examConfigId: number) =>
  useQuery<ExamConfigI>({
    queryKey: ["examConfigById", examConfigId],
    queryFn: () => apiClient.get(`/exams/config/${examConfigId}`),
    enabled: !!examConfigId,
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      const doneStates: ExamWorkflowStatus[] = [
        "warning_handling",
        "validation",
        "completed",
        "sent",
      ];
      return state && doneStates.includes(state) ? false : 5000;
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
    onError: () =>
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      }),
  });
};

const usePostGrades = (examConfigId: number) =>
  useMutation({
    mutationFn: (options: PostEmailI) =>
      apiClient.post(`/exams/${examConfigId}/session/notify-students`, options),
    onSuccess: () => {
      toast.dismiss();
      toast.success("Notas lançadas com sucesso!", {
        position: "top-right",
        duration: 3000,
      });
    },
    onError: () => {
      toast.dismiss();
      toast.error("Ocorreu um erro ao lançar as notas.", {
        position: "top-right",
        duration: 3000,
      });
    },
  });

const useStartExamSession = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.patch(`/exams/${examConfigId}/session/start`, {}),
    onSuccess: () => {
      toast.success("Exame iniciado com sucesso!", { position: "top-right" });
      queryClient.invalidateQueries({ queryKey: ["examConfig"] });
      queryClient.invalidateQueries({
        queryKey: ["examSession", examConfigId],
      });
    },
    onError: () =>
      toast.error("Erro ao iniciar o exame.", { position: "top-right" }),
  });
};

const usePatchExamVigilants = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vigilantKeycloakIds: string[]) =>
      apiClient.patch(`/exams/${examConfigId}/vigilantes`, {
        vigilant_keycloak_ids: vigilantKeycloakIds,
      }),
    onSuccess: () => {
      toast.success("Vigilantes guardados!", { position: "top-right" });
      queryClient.invalidateQueries({
        queryKey: ["examConfigById", examConfigId],
      });
    },
    onError: () =>
      toast.error("Erro ao guardar vigilantes.", { position: "top-right" }),
  });
};

const useCloseExamSession = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.patch(`/exams/${examConfigId}/session/close`, {}),
    onSuccess: () => {
      toast.success("Exame fechado com sucesso!", { position: "top-right" });
      queryClient.invalidateQueries({ queryKey: ["examConfig"] });
      queryClient.invalidateQueries({
        queryKey: ["examSession", examConfigId],
      });
    },
    onError: () =>
      toast.error("Erro ao fechar o exame.", { position: "top-right" }),
  });
};

const useDownloadGrades = (examConfigId: number) =>
  useMutation({
    mutationFn: () =>
      apiClient.download(`/exams/${examConfigId}/grades/download`),
    onSuccess: (blob: Blob) => saveFile(blob, "notas.ods"),
    onError: () =>
      toast.error("Erro ao descarregar as notas.", { position: "top-right" }),
  });

const useGetExamSessions = ({ enabled = true }: { enabled: boolean }) =>
  useQuery<GetExamSessionI[]>({
    queryKey: ["examSessions"],
    queryFn: () => apiClient.get("/exams/professor/my-exam-sessions"),
    enabled,
  });

const useGetExamSessionInfo = (examConfigId: number) =>
  useQuery<GetExamSessionInfoI>({
    queryKey: ["examSession", examConfigId],
    queryFn: () => apiClient.get(`/exams/${examConfigId}/session/info`),
  });

const useGetExamSessionMetrics = ({
  enabled = true,
  examConfigId,
  refetchInterval,
}: {
  enabled: boolean;
  examConfigId: number;
  refetchInterval?: number;
}) =>
  useQuery<GetExamSessionMetricsI>({
    queryKey: ["examSessionMetrics", examConfigId],
    queryFn: () => apiClient.get(`/exams/${examConfigId}/session/metrics`),
    enabled,
    refetchInterval,
  });

const usePostPairExamStudent = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (props: PostExamStudentI) =>
      apiClient.post(`/exams/${examConfigId}/session/student_to_exam`, props),
    onSuccess: () => {
      toast.success("Aluno associado a exame com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({
        queryKey: ["examSessionMetrics", examConfigId],
      });
    },
    onError: () =>
      toast.error("Ocorreu um erro, tente novamente.", {
        position: "top-right",
      }),
  });
};

const useSendExamsPhotos = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (files: string[]) =>
      apiClient.post(`/exams/${examConfigId}/session/evaluate`, { files }),
    onSuccess: () => {
      toast.success("A foto do exame foi enviada com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({
        queryKey: ["examSession", examConfigId],
      });
      queryClient.invalidateQueries({
        queryKey: ["submittedExams", examConfigId],
      });
    },
    onError: () =>
      toast.error("Ocorreu um erro, tente novamente.", {
        position: "top-right",
      }),
  });
};

const useGetSubmittedExams = (examConfigId: number) =>
  useQuery<{ submitted_count: number }>({
    queryKey: ["submittedExams", examConfigId],
    queryFn: () =>
      apiClient.get(`/exams/${examConfigId}/session/submitted_count`),
  });

const useGetWarnings = (examConfigId: number) =>
  useQuery<{ students: StudentsI[]; warnings: GetWarningsI[] }>({
    queryKey: ["warnings", examConfigId],
    queryFn: () => apiClient.get(`/warnings/${examConfigId}/`),
  });

const useResolveWarnings = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (props: PostResolveWarningsI) =>
      apiClient.post(`/warnings/${examConfigId}/resolve`, props),
    onSuccess: () => {
      toast.success("Aluno associado a exame com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["warnings", examConfigId] });
    },
    onError: () =>
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      }),
  });
};

const useGetExamsResponses = (examConfigId: number, refetchInterval?: number) =>
  useQuery<ExamResponseI[]>({
    queryKey: ["exams_responses", examConfigId],
    queryFn: () => apiClient.get(`/exams/${examConfigId}/all_exams_info`),
    refetchInterval,
  });

const useGetExamInfo = (examId: number | null) =>
  useQuery<ExamResponseI>({
    queryKey: ["exam_info", examId],
    queryFn: () => apiClient.get(`/exams/${examId}/exam_info`),
    enabled: examId !== null,
  });

const useValidateExam = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (examId: number) =>
      apiClient.post(`/exams/${examId}/validate`, { exam_id: examId }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["exams_responses", examConfigId],
      });
    },
    onError: () =>
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      }),
  });
};

const useCorrectExam = (examConfigId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      examId,
      props,
    }: {
      examId: number;
      props: ExamCorrectionI;
    }) => apiClient.post(`/exams/${examId}/correct_by_hand_job`, props),
    onSuccess: () => {
      toast.success("Exame corrigido com sucesso!", { position: "top-right" });
      queryClient.invalidateQueries({
        queryKey: ["exams_responses", examConfigId],
      });
    },
    onError: () =>
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      }),
  });
};

export {
  useAddExamConfig,
  useDownloadExamConfig,
  useGetExamConfig,
  useGetExamConfigById,
  useDeleteExamConfig,
  usePostGrades,
  useStartExamSession,
  usePatchExamVigilants,
  useCloseExamSession,
  useDownloadGrades,
  useGetExamSessions,
  useGetExamSessionInfo,
  useGetExamSessionMetrics,
  usePostPairExamStudent,
  useSendExamsPhotos,
  useGetSubmittedExams,
  useGetWarnings,
  useResolveWarnings,
  useGetExamsResponses,
  useGetExamInfo,
  useValidateExam,
  useCorrectExam,
};
