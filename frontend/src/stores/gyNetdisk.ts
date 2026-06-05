import { defineStore } from "pinia";
import { ref } from "vue";
import type {
  AuthStatus,
  BreadcrumbItem,
  CloudTask,
  GyFile,
  UserInfo,
} from "@/types/gyNetdisk";
import * as gyApi from "@/api/modules/gyNetdisk";

export const useGyNetdiskStore = defineStore("gyNetdisk", () => {
  // ── Auth state ───────────────────────────────────────────
  const isAuthenticated = ref(false);
  const user = ref<UserInfo | null>(null);
  const authStep = ref<1 | 2 | 3 | 4>(1);
  const phone = ref("");
  const captchaToken = ref<string | null>(null);
  const verificationId = ref<string | null>(null);

  // ── File state ───────────────────────────────────────────
  const files = ref<GyFile[]>([]);
  const currentParentId = ref("");
  const breadcrumb = ref<BreadcrumbItem[]>([{ id: "", name: "根目录" }]);
  const loading = ref(false);
  const total = ref(0);

  // ── Cloud download state ────────────────────────────────
  const cloudTasks = ref<CloudTask[]>([]);
  const showCloudDialog = ref(false);
  const cloudUrl = ref("");
  const cloudLoading = ref(false);
  const cloudFolderId = ref("");
  const cloudMessage = ref<{ text: string; type: "success" | "error" } | null>(null);

  // ── Auth actions ─────────────────────────────────────────

  async function checkAuth() {
    try {
      const status: AuthStatus = await gyApi.getAuthStatus();
      isAuthenticated.value = status.authenticated;
      if (status.authenticated) {
        user.value = await gyApi.getUserInfo();
      }
    } catch {
      isAuthenticated.value = false;
    }
  }

  async function initLogin(phoneNumber: string) {
    const res = await gyApi.smsInit(phoneNumber);
    phone.value = phoneNumber;
    captchaToken.value = res.captcha_token ?? null;
    authStep.value = 2;
    return res;
  }

  async function sendCode() {
    const res = await gyApi.smsSend(phone.value, captchaToken.value);
    verificationId.value = res.verification_id ?? null;
    authStep.value = 3;
    return res;
  }

  async function verifyCode(code: string) {
    const res = await gyApi.smsVerify(code);
    authStep.value = 4;
    return res;
  }

  async function completeLogin(
    code: string,
    verificationToken: string,
  ) {
    const res = await gyApi.smsSignin(code, verificationToken, captchaToken.value);
    isAuthenticated.value = true;
    user.value = await gyApi.getUserInfo();
    authStep.value = 1;
    return res;
  }

  // ── File actions ─────────────────────────────────────────

  async function loadFiles(parentId = "", fileType?: string | null) {
    loading.value = true;
    try {
      const res = await gyApi.listFiles(parentId, fileType);
      files.value = res.files;
      total.value = res.total;
      currentParentId.value = parentId;
    } finally {
      loading.value = false;
    }
  }

  function navigateTo(item: BreadcrumbItem) {
    const idx = breadcrumb.value.findIndex((b) => b.id === item.id);
    if (idx >= 0) {
      breadcrumb.value = breadcrumb.value.slice(0, idx + 1);
    }
    loadFiles(item.id);
  }

  function enterFolder(folderId: string, folderName: string) {
    breadcrumb.value.push({ id: folderId, name: folderName });
    loadFiles(folderId);
  }

  // ── Cloud download actions ───────────────────────────────

  async function fetchCloudTasks() {
    try {
      const res = await gyApi.listCloudTasks();
      cloudTasks.value = res.data?.list ?? [];
    } catch {
      cloudTasks.value = [];
    }
  }

  async function submitCloudDownload() {
    const text = cloudUrl.value.trim();
    if (!text) return;
    cloudLoading.value = true;
    cloudMessage.value = null;
    try {
      const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
      if (lines.length <= 1) {
        await gyApi.cloudDownload(lines[0]);
        cloudMessage.value = { text: "已提交，任务已添加到列表", type: "success" };
      } else {
        const res = await gyApi.cloudDownloadBatch(text);
        cloudMessage.value = {
          text: `提交完成：成功 ${res.ok} 条，失败 ${res.fail} 条，共 ${res.total} 条`,
          type: res.fail === 0 ? "success" : "error",
        };
      }
      cloudUrl.value = "";
      await fetchCloudTasks();
    } catch (e: any) {
      cloudMessage.value = { text: e?.response?.data?.detail || e.message || "提交失败", type: "error" };
    } finally {
      cloudLoading.value = false;
    }
  }

  async function retryTask(taskId: string) {
    await gyApi.retryCloudTask(taskId);
    await fetchCloudTasks();
  }

  async function deleteTasks(taskIds: string[]) {
    await gyApi.deleteCloudTasks(taskIds);
    await fetchCloudTasks();
  }

  async function loadCloudFolder() {
    try {
      const res = await gyApi.getCloudFolder();
      cloudFolderId.value = res.folder_id ?? "";
    } catch {
      cloudFolderId.value = "";
    }
  }

  async function saveCloudFolder(folderId: string) {
    await gyApi.setCloudFolder(folderId);
    cloudFolderId.value = folderId;
  }

  return {
    // auth
    isAuthenticated,
    user,
    authStep,
    phone,
    captchaToken,
    verificationId,
    checkAuth,
    initLogin,
    sendCode,
    verifyCode,
    completeLogin,
    // files
    files,
    currentParentId,
    breadcrumb,
    loading,
    total,
    loadFiles,
    navigateTo,
    enterFolder,
    // cloud
    cloudTasks,
    showCloudDialog,
    cloudUrl,
    cloudLoading,
    cloudFolderId,
    cloudMessage,
    fetchCloudTasks,
    submitCloudDownload,
    retryTask,
    deleteTasks,
    loadCloudFolder,
    saveCloudFolder,
  };
});
