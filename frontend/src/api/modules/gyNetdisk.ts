import api from "@/api";
import type {
  AuthStatus,
  CloudTaskListResponse,
  GyFileListResponse,
  UserInfo,
} from "@/types/gyNetdisk";

// ── Auth ──────────────────────────────────────────────────

export function getAuthStatus(): Promise<AuthStatus> {
  return api.get("/gy/auth/status");
}

export function smsInit(phoneNumber: string, captchaToken?: string | null): Promise<any> {
  const form = new FormData();
  form.append("phone_number", phoneNumber);
  if (captchaToken) form.append("captcha_token", captchaToken);
  return api.post("/gy/auth/sms/init", form);
}

export function smsSend(
  phoneNumber: string,
  captchaToken?: string | null,
  target = "ANY",
): Promise<any> {
  const form = new FormData();
  form.append("phone_number", phoneNumber);
  if (captchaToken) form.append("captcha_token", captchaToken);
  form.append("target", target);
  return api.post("/gy/auth/sms/send", form);
}

export function smsVerify(verificationCode: string): Promise<any> {
  const form = new FormData();
  form.append("verification_code", verificationCode);
  return api.post("/gy/auth/sms/verify", form);
}

export function smsSignin(
  verificationCode: string,
  verificationToken: string,
  captchaToken?: string | null,
): Promise<any> {
  const form = new FormData();
  form.append("verification_code", verificationCode);
  form.append("verification_token", verificationToken);
  if (captchaToken) form.append("captcha_token", captchaToken);
  return api.post("/gy/auth/sms/signin", form);
}

export function refreshToken(): Promise<any> {
  return api.post("/gy/auth/refresh");
}

export function getUserInfo(): Promise<UserInfo> {
  return api.get("/gy/auth/user");
}

// ── Files ─────────────────────────────────────────────────

export function listFiles(
  parentId = "",
  fileType?: string | null,
  page = 1,
  pageSize = 50,
): Promise<GyFileListResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (parentId) params.parent_id = parentId;
  if (fileType) params.type = fileType;
  return api.get("/gy/files", { params });
}

export function getFileDetail(fileId: string) {
  return api.get(`/gy/files/${fileId}`);
}

export function getDownloadUrl(fileId: string): Promise<{ download_url: string }> {
  return api.post(`/gy/files/download?file_id=${fileId}`);
}

export function cloudDownload(url: string, parentId = "") {
  const form = new FormData();
  form.append("url", url);
  if (parentId) form.append("parent_id", parentId);
  return api.post("/gy/files/cloud-download", form);
}

export function cloudDownloadBatch(
  urls: string,
  parentId = "",
): Promise<{ results: Array<{ url: string; status: string; detail?: string }>; total: number; ok: number; fail: number }> {
  const form = new FormData();
  form.append("urls", urls);
  if (parentId) form.append("parent_id", parentId);
  return api.post("/gy/files/cloud-download-batch", form, { timeout: 0 });
}

export function listCloudTasks(
  status?: number[] | null,
  pageSize = 50,
): Promise<CloudTaskListResponse> {
  const params: Record<string, unknown> = { page_size: pageSize };
  if (status) params.status = status;
  return api.get("/gy/files/cloud-tasks", { params });
}

export function retryCloudTask(taskId: string) {
  return api.post(`/gy/files/cloud-tasks/${taskId}/retry`);
}

export function deleteCloudTasks(taskIds: string[]) {
  return api.delete("/gy/files/cloud-tasks", { data: taskIds });
}

export function getCloudFolder(): Promise<{ folder_id: string }> {
  return api.get("/gy/files/config/cloud-folder");
}

export function setCloudFolder(folderId: string) {
  const form = new FormData();
  form.append("folder_id", folderId);
  return api.put("/gy/files/config/cloud-folder", form);
}

// ── Magnets ─────────────────────────────────────────────

export interface MagnetItem {
  id: number;
  bangou: string;
  title: string;
  magnet: string;
  downloaded: boolean;
  downloaded_at: string;
  created_at: string;
}

export interface MagnetListResponse {
  items: MagnetItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MagnetImportResult {
  imported: number;
  skipped: number;
  total: number;
}

export function importMagnets(file: File): Promise<MagnetImportResult> {
  const form = new FormData();
  form.append("file", file);
  return api.post("/gy/magnets/import", form, { timeout: 0 });
}

export function listMagnets(
  params: { page?: number; page_size?: number; keyword?: string } = {},
): Promise<MagnetListResponse> {
  return api.get("/gy/magnets", { params });
}

export function getMagnet(bangou: string): Promise<MagnetItem> {
  return api.get(`/gy/magnets/${encodeURIComponent(bangou)}`);
}

export function deleteMagnets(ids: number[]) {
  return api.delete("/gy/magnets", { data: { ids } });
}

// ── Daily Import ───────────────────────────────────────

export interface DailyImportConfig {
  hour: number;
  count: number;
  enabled: boolean;
}

export interface DailyImportStatus {
  enabled: boolean;
  hour: number;
  count: number;
  is_running: boolean;
  last_run_time: string;
  last_run_results: Array<{ bangou: string; status: string; detail?: string }>;
  next_run: string;
  total_undownloaded: number;
  total_downloaded: number;
}

export function getDailyImportConfig(): Promise<DailyImportConfig> {
  return api.get("/gy/daily-import/config");
}

export function saveDailyImportConfig(
  hour: number,
  count: number,
  enabled = true,
): Promise<DailyImportConfig> {
  return api.put("/gy/daily-import/config", { hour, count, enabled });
}

export function getDailyImportStatus(): Promise<DailyImportStatus> {
  return api.get("/gy/daily-import/status");
}

export function triggerDailyImport(): Promise<{
  results: Array<{ bangou: string; status: string; detail?: string }>;
  message: string;
}> {
  return api.post("/gy/daily-import/run", null, { timeout: 0 });
}
