import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import { type NewUcI, type UcI } from "@/lib/types";
import { useNavigate } from "@tanstack/react-router";

const useGetUc = () =>
  useQuery<UcI[]>({
    queryKey: ["uc"],
    queryFn: () => apiClient.get("/subjects/"),
  });

const useAddUc = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationKey: ["addUc"],
    mutationFn: (props: NewUcI) => apiClient.post("/subjects/", props),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uc"] });
      navigate({ to: "/unidades-curriculares" });
    },
  });
};

const useGetUcById = (ucId: number) =>
  useQuery<UcI>({
    queryKey: ["uc", ucId],
    queryFn: () => apiClient.get(`/subjects/${ucId}/`),
    enabled: !!ucId,
  });

const useGetUcStudents = (ucId: number) =>
  useQuery<UserI[]>({
    queryKey: ["uc", ucId, "students"],
    queryFn: () => apiClient.get(`/subjects/${ucId}/students`),
    enabled: !!ucId,
  });

const useGetUcProfessors = (ucId: number) =>
  useQuery<UserI[]>({
    queryKey: ["uc", ucId, "professors"],
    queryFn: () => apiClient.get(`/subjects/${ucId}/professors`),
    enabled: !!ucId,
  });

const useGetUcRegent = (ucId: number) =>
  useQuery<UserI>({
    queryKey: ["uc", ucId, "regent"],
    queryFn: () => apiClient.get(`/subjects/${ucId}/regent`),
    enabled: !!ucId,
  });

const useDeleteUcById = (ucId: number) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationKey: ["deleteUc", ucId],
    mutationFn: (ucId: number) => apiClient.delete(`/subjects/${ucId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uc"] });
      navigate({ to: "/unidades-curriculares" });
    },
  });
};

const useUpdateUc = (ucId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["updateUc", ucId],
    mutationFn: (data: { regent_keycloak_id?: string; student_keycloak_ids?: string[]; professor_keycloak_ids?: string[] }) => 
      apiClient.put(`/subjects/${ucId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uc", ucId] });
      queryClient.invalidateQueries({ queryKey: ["uc", ucId, "students"] });
      queryClient.invalidateQueries({ queryKey: ["uc", ucId, "professors"] });
      queryClient.invalidateQueries({ queryKey: ["uc", ucId, "regent"] });
    },
  });
};

export { useGetUc, useAddUc, useGetUcById, useDeleteUcById, useGetUcStudents, useGetUcProfessors, useGetUcRegent, useUpdateUc };
