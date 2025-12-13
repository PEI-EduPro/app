import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import { type NewExamConfigI, type ExamConfigI } from "@/lib/types";

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
    onError: (error) => {
      console.error("Exam generation and download failed:", error.message);
    },
  });
};

const useGetExamConfig = (ucId: number) =>
  useQuery<ExamConfigI[]>({
    queryKey: ["examConfig", ucId],
    queryFn: () => apiClient.get(`/exams/subject/${ucId}/configs`),
    enabled: !!ucId,
  });

export { useAddExamConfig, useGetExamConfig };
