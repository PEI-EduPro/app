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
  topics: string[];
  number_questions: Record<string, number>;
  relative_quotations: Record<string, number>;
  exam_title: string;
  exam_date: string;
  semester: string;
  academic_year: string;
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

export interface TopicI {
  id: number;
  name: string;
  subject_id: number;
}

export type GetTopicI = [TopicI, number];
