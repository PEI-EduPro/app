import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import {
  type ExamCorrectionI,
  type ExamResponseI,
  type GetWaintingRoomByIdI,
  type GetWaitingRoomI,
  type GetWaitingRoomMetricsI,
  type GetWarningsI,
  type PostExamStudentI,
  type PostResolveWarningsI,
  type StudentsI,
} from "@/lib/types";
import { toast } from "sonner";

const useGetWaitingRooms = ({ enabled = true }: { enabled: boolean }) =>
  useQuery<GetWaitingRoomI[]>({
    queryKey: ["waitingRooms"],
    queryFn: () => apiClient.get("/waiting-rooms/professor/my-waiting-rooms"),
    enabled,
  });

const useGetWaitingRoomById = (roomId: number) =>
  useQuery<GetWaintingRoomByIdI>({
    queryKey: ["waitingRoom", roomId],
    queryFn: () => apiClient.get(`/waiting-rooms/${roomId}/info`),
  });

const useGetWaitingRoomMetrics = ({
  enabled = true,
  roomId,
  refetchInterval,
}: {
  enabled: boolean;
  roomId: number;
  refetchInterval?: number;
}) =>
  useQuery<GetWaitingRoomMetricsI>({
    queryKey: ["metrics", roomId],
    queryFn: () => apiClient.get(`/waiting-rooms/${roomId}/metrics`),
    enabled,
    refetchInterval,
  });

const usePostPairExamStudent = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["student_to_exam"],
    mutationFn: (props: PostExamStudentI) =>
      apiClient.post(`/waiting-rooms/${roomId}/student_to_exam`, props),
    onSuccess: () => {
      toast.success("Aluno associado a exame com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["metrics", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const useStartWaitingRoom = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["start_waiting_room"],
    mutationFn: () => apiClient.patch(`/waiting-rooms/${roomId}/start`, {}),
    onSuccess: () => {
      toast.success("Exame foi inicializado com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["metrics", roomId] });
      queryClient.invalidateQueries({ queryKey: ["waitingRoom", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const useCloseWaitingRoom = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["close_waiting_room"],
    mutationFn: () => apiClient.patch(`/waiting-rooms/${roomId}/close`, {}),
    onSuccess: () => {
      toast.success("Exame foi terminado com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["metrics", roomId] });
      queryClient.invalidateQueries({ queryKey: ["waitingRoom", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const useSendExamsPhotos = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["send_exams_photos"],
    mutationFn: (files: string[]) =>
      apiClient.post(`/waiting-rooms/${roomId}/evaluate`, { files }),
    onSuccess: () => {
      toast.success("As fotos dos exames enviadas com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["waitingRoom", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const useGetWarnings = (roomId: number) =>
  useQuery<{ students: StudentsI[]; warnings: GetWarningsI[] }>({
    queryKey: ["warnings", roomId],
    queryFn: () => apiClient.get(`/warnings/${roomId}/`),
  });

const useResolveWarnings = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["resolve_warnings", roomId],
    mutationFn: (props: PostResolveWarningsI) =>
      apiClient.post(`/warnings/${roomId}/resolve`, props),
    onSuccess: () => {
      toast.success("Aluno associado a exame com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["warnings", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const useGetExamsResponses = (roomId: number) =>
  useQuery<ExamResponseI[]>({
    queryKey: ["exams_responses", roomId],
    queryFn: () => apiClient.get(`/exams/${roomId}/all_exams_info`),
  });

const useValidateExam = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["validate_exam", roomId],
    mutationFn: (examId: number) =>
      apiClient.post(`/exams/${examId}/validate`, { exam_id: examId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams_responses", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

const useCorrectExam = (roomId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["correct_exam", roomId],
    mutationFn: ({
      examId,
      props,
    }: {
      examId: number;
      props: ExamCorrectionI;
    }) => apiClient.post(`/exams/${examId}/correct_by_hand_job`, props),
    onSuccess: () => {
      toast.success("Exame corrigido com sucesso!", {
        position: "top-right",
      });
      queryClient.invalidateQueries({ queryKey: ["exams_responses", roomId] });
    },
    onError: () => {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    },
  });
};

export {
  useGetWaitingRooms,
  useGetWaitingRoomById,
  useGetWaitingRoomMetrics,
  usePostPairExamStudent,
  useStartWaitingRoom,
  useCloseWaitingRoom,
  useSendExamsPhotos,
  useGetWarnings,
  useResolveWarnings,
  useGetExamsResponses,
  useValidateExam,
  useCorrectExam,
};
