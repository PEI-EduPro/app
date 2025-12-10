import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import { type NewUc, type UcI } from "@/lib/types";
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
    mutationFn: (props: NewUc) => apiClient.post("/subjects/", props),
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

// const useGetUcQuestionsById = (ucId: number) =>
//   useQuery<UcI>({
//     queryKey: ["uc", ucId],
//     queryFn: () => apiClient.get(`/subjects/${ucId}/all-questions`)
//   })

// export { useGetUc, useAddUc, useGetUcById, useDeleteUcById , useGetUcQuestionsById };
export { useGetUc, useAddUc, useGetUcById, useDeleteUcById};
