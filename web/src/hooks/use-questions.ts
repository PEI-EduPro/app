import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { GetTopicI } from "@/lib/types";

export function useSubject(subjectId: number) {
  return useQuery({
    queryKey: ["subject", subjectId],
    queryFn: async () => {
      const data = await apiClient.get<{ subject_name: string }>(`/subjects/${subjectId}/all-questions`);
      return { name: data.subject_name };
    },
    enabled: !!subjectId,
  });
}

export function useQuestions(subjectId: number) {
  return useQuery({
    queryKey: ["questions", subjectId],
    queryFn: () => apiClient.get(`/subjects/${subjectId}/all-questions`),
    enabled: !!subjectId,
  });
}

export function useCreateTopic(subjectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiClient.post("/topics/", { name, subject_id: subjectId }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] }),
  });
}

export function useUpdateTopic(subjectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      apiClient.put(`/topics/${id}`, { name, subject_id: subjectId }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] }),
  });
}

export function useDeleteTopic(subjectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/topics/${id}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] }),
  });
}

export function useCreateQuestion(subjectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { questions: any[]; options: any[] }) => {
      const questions: any[] = await apiClient.post(
        "/questions/",
        data.questions
      );
      if (data.options.length > 0 && questions.length > 0) {
        const optionsWithQuestionId = data.options.map((opt) => ({
          ...opt,
          question_id: questions[0].id,
        }));
        await apiClient.post("/question-options/", optionsWithQuestionId);
      }
      return questions;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] }),
  });
}

export function useUpdateQuestion(subjectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
      toUpdate,
      toCreate,
      toDelete,
    }: {
      id: number;
      data: any;
      toUpdate?: Array<{ id: number; option_text: string; value: boolean }>;
      toCreate?: Array<{
        question_id: number;
        option_text: string;
        value: boolean;
      }>;
      toDelete?: number[];
    }) => {
      await apiClient.put(`/questions/${id}`, data);
      if (toUpdate?.length) {
        await Promise.all(
          toUpdate.map((opt) =>
            apiClient.put(`/question-options/${opt.id}`, {
              option_text: opt.option_text,
              value: opt.value,
            })
          )
        );
      }
      if (toCreate?.length) {
        await apiClient.post("/question-options/", toCreate);
      }
      if (toDelete?.length) {
        await Promise.all(
          toDelete.map((optId) =>
            apiClient.delete(`/question-options/${optId}`)
          )
        );
      }
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] }),
  });
}

export function useDeleteQuestion(subjectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/questions/${id}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] }),
  });
}

export function useGetUCTopics(ucId: number) {
  return useQuery({
    queryKey: ["ucTopics", ucId],
    queryFn: async () => {
      const response = await apiClient.get<GetTopicI[]>(
        `/subjects/${ucId}/topics`
      );
      return response;
    },

    enabled: !!ucId,
  });
}
