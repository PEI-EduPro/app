import type { UseFormReturn } from "react-hook-form";
import type { NewExamConfigI, GetTopicI } from "@/lib/types";

export interface StepProps {
  form: UseFormReturn<NewExamConfigI>;
  onNext: () => void;
  onPrev: () => void;
  onClose: () => void;
}

export interface Step0Props extends StepProps {
  topics: GetTopicI[] | undefined;
  selectedTopics: { id: string; nome: string }[];
  setSelectedTopics: (v: { id: string; nome: string }[]) => void;
}

export interface Step1Props extends StepProps {
  topics: GetTopicI[] | undefined;
  selectedTopics: { id: string; nome: string }[];
}

export interface Step2Props extends StepProps {
  selectedTopics: { id: string; nome: string }[];
}

export interface Step4Props extends StepProps {
  studentsCsv: File | null;
  setStudentsCsv: (f: File | null) => void;
  isPending: boolean;
}

export interface Step5Props {
  form: UseFormReturn<NewExamConfigI>;
  topics: GetTopicI[] | undefined;
  onPrev: () => void;
  onSubmit: () => void;
  isPending: boolean;
}
