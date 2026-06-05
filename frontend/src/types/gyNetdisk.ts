export interface GyFile {
  file_id: string;
  name: string;
  type: string;
  size: number;
  created_at: string;
  updated_at: string;
  ext: string;
  mime_type: string;
  thumbnail: string;
}

export interface GyFileListResponse {
  files: GyFile[];
  total: number;
  page: number;
  page_size: number;
}

export interface CloudTask {
  taskId: string;
  url: string;
  fileName: string;
  fileSize: number;
  status: number;
  progress: number;
  createTime: string;
}

export interface CloudTaskListResponse {
  data: {
    list: CloudTask[];
    total: number;
  };
}

export interface AuthStatus {
  authenticated: boolean;
  has_refresh_token: boolean;
  phone: string | null;
}

export interface UserInfo {
  nickname?: string;
  phone_number?: string;
  [key: string]: unknown;
}

export interface BreadcrumbItem {
  id: string;
  name: string;
}
