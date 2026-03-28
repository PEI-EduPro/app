import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import {
  type GetWaintingRoomByIdI,
  type GetWaitingRoomI,
  type GetWaitingRoomMetricsI,
  type PostExamStudentI,
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

export {
  useGetWaitingRooms,
  useGetWaitingRoomById,
  useGetWaitingRoomMetrics,
  usePostPairExamStudent,
  useStartWaitingRoom,
  useCloseWaitingRoom,
};
