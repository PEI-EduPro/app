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
      queryClient.invalidateQueries({ queryKey: ["product"] });
      navigate({ to: "/unidades-curriculares" });
    },
  });
};

export { useGetUc, useAddUc };
