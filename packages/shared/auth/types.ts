export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type UserPublic = {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};

export type ApiErrorPayload = {
  detail?: string | Array<{ msg?: string; loc?: string[] }>;
};
