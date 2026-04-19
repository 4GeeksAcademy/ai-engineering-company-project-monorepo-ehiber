export interface CandidateRecord {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url: string | null;
  cv_url: string | null;
  status: string;
  stage: string;
  experience_years: number;
  notes_count: number;
  applied_at: string;
  updated_at: string;
}

export interface CandidateRecordCreate {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url?: string;
  cv_url?: string;
  experience_years: number;
}

export interface CandidateRecordPatch {
  status?: string;
  stage?: string;
}

export interface CandidateNote {
  id: string;
  record_id: string;
  content: string;
  created_at: string;
}

export interface CandidateListResponse {
  total: number;
  page: number;
  limit: number;
  data: CandidateRecord[];
}

export interface CandidateNotesResponse {
  data: CandidateNote[];
  meta: {
    total: number;
  };
}

export interface CandidateListFilters {
  status?: string;
  stage?: string;
  search?: string;
  page?: number;
}

export interface CandidateFormValues {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url: string;
  cv_url: string;
  experience_years: string;
}

export interface CandidateFormErrors {
  full_name?: string;
  email?: string;
  phone?: string;
  position?: string;
  linkedin_url?: string;
  cv_url?: string;
  experience_years?: string;
}

export interface FeedbackMessage {
  type: "success" | "error";
  text: string;
}
