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
  topics: string[];
  number_questions: Record<string, number>;
  relative_quotations: Record<string, number>;
  exam_title: string;
  exam_date: string;
  semester: string;
  academic_year: string;
  vigilant_keycloak_ids: string[];
  student_tuples: Array<Array<string>>;
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

export interface GetWaitingRoomI {
  subject_id: number;
  subject_name: string;
  waiting_room_id: number;
  state: WaitingRoomStatusT;
  role: "regent" | "vigilant";
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
