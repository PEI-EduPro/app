import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import { type UserI } from "@/lib/types";

export const useGetProfessors = () =>
  useQuery<UserI[]>({
    queryKey: ["professors"],
    queryFn: () => apiClient.get("/users/professors"),
  });

export const useGetStudents = () =>
  useQuery<UserI[]>({
    queryKey: ["students"],
    queryFn: () => apiClient.get("/users/students"),
  });
