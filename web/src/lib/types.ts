export interface UcI {
  id: number;
  name: string;
}

export interface NewUcI {
  name: string;
  regent_keycloak_id: string;
  student_keycloak_ids?: string[];
  professor_keycloak_ids?: string[];
}

export interface UserI {
  id: string;
  username?: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  first_name?: string;
  last_name?: string;
}

export interface NewExamConfigI {
  subject_id: number;
  fraction: number;
  num_variations: number;
  num_versions: number;
  topics: string[];
  number_questions: Record<number, number>;
  relative_quotations: Record<number, number>;
  exam_title: string;
  exam_date: string;
  semester: string;
  academic_year: string;
  vigilant_keycloak_ids: string[];
  student_tuples: Array<Array<string>>;
}

export type GenerationStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface ExamConfigI {
  id: number;
  subject_id: number;
  fraction: number;
  num_variations: number;
  status: GenerationStatus;
  topic_configs: {
    topic_id: number;
    topic_name: string;
    num_questions: number;
    relative_weight: number;
  }[];
}

export interface TopicI {
  id: number;
  name: string;
  subject_id: number;
}

export type GetTopicI = [TopicI, number];

export interface GetWaitingRoomI {
  subject_id: number;
  subject_name: string;
  waiting_room_id: number;
  state: WaitingRoomStatusT;
  role: "regent" | "vigilant";
  exam_name: string;
}

export type WaitingRoomStatusT = "preparation" | "running" | "closed";

export interface GetWaintingRoomByIdI {
  id: number;
  exam_config_id: number;
  state: WaitingRoomStatusT;
  student_list: { name: string; nmec: number }[];
  exam_ids: number[];
  total_students: number;
  total_exams: number;
  subject_name: string;
  role: "regent" | "vigilant";
}

export interface GetWaitingRoomMetricsI {
  associated_exams_count: number;
  associated_students_count: number;
}

export interface PostExamStudentI {
  qr: string;
  nmec: number;
}

export interface StudentsI {
  nmec: number;
  name: string;
  email: string;
}

export interface GetWarningsI {
  exam_id: number;
  batch_number: number;
  students: [
    {
      nmec: number;
      name: string;
      email: string;
    },
  ];
}

export interface ResolveWarningsI {
  exam_id: number;
  student_nmec: string;
}

export interface PostResolveWarningsI {
  assignments: ResolveWarningsI[];
}

export interface QuestionsI {
  question_number: number;
  correct_answer: "a" | "b" | "c" | "d";
  discount: number;
  value: number;
  answers: { a: boolean; b: boolean; c: boolean; d: boolean };
}

export interface ExamResponseI {
  exam_id: number;
  questions: QuestionsI[] | null;
  grade: number | null;
  capture: string | null;
  corrected: boolean;
  validated: boolean;
}

export type OptionKey = "a" | "b" | "c" | "d";

export interface ExamCorrectionI {
  grid: Record<number, Record<OptionKey, boolean>>;
}
