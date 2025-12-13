export interface UcI {
  id: number;
  name: string;
}

export interface NewUcI {
  name: string;
}

export interface NewExamConfigI {
  subject_id: number;
  fraction: number;
  num_variations: number;
  topics: number[];
  number_questions: Record<number, number>;
  relative_quotations: Record<number, number>;
}

export interface ExamConfigI {
  id: number;
  subject_id: number;
  fraction: number;
  num_variations: number;
  topic_configs: {
    topic_id: number;
    topic_name: string;
    number_questions: number;
    relative_weight: number;
  }[];
}
