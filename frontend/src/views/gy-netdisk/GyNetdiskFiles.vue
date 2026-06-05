<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useGyNetdiskStore } from "@/stores/gyNetdisk";
import { useFormatSize } from "@/composables/useFormatSize";
import { useRelativeTime } from "@/composables/useRelativeTime";
import { getDownloadUrl } from "@/api/modules/gyNetdisk";

const router = useRouter();
const store = useGyNetdiskStore();
const editingFolder = ref(false);
const folderInput = ref("");

const TYPE_ICONS: Record<string, string> = {
  folder: "📁",
  image: "🖼️",
  video: "🎬",
  audio: "🎵",
  document: "📄",
  archive: "📦",
  subtitle: "💬",
  disc: "💿",
  file: "📎",
};

const TASK_STATUS: Record<number, { label: string; color: string }> = {
  1: { label: "等待中", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  2: { label: "下载中", color: "bg-blue-100 text-blue-800 border-blue-200" },
  3: { label: "已完成", color: "bg-green-100 text-green-800 border-green-200" },
  5: { label: "失败", color: "bg-red-100 text-red-800 border-red-200" },
};

onMounted(async () => {
  await store.checkAuth();
  if (!store.isAuthenticated) {
    router.replace("/tools/gy-netdisk/login");
    return;
  }
  store.loadFiles();
  store.fetchCloudTasks();
  store.loadCloudFolder();
});

watch(
  () => store.showCloudDialog,
  (v) => {
    if (v) {
      store.fetchCloudTasks();
      store.cloudMessage = null;
    }
  },
);

async function handleDownload(fileId: string) {
  try {
    const res = await getDownloadUrl(fileId);
    if (res.download_url) window.open(res.download_url, "_blank");
  } catch (e: any) {
    alert(e.message);
  }
}
</script>

<template>
  <div v-if="!store.isAuthenticated" class="text-center py-20 text-green-600">
    检查登录状态中...
  </div>

  <template v-else>
    <!-- Top bar -->
    <div
      class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6"
    >
      <!-- Breadcrumb -->
      <nav class="flex items-center gap-1 text-sm flex-wrap">
        <template v-for="(item, i) in store.breadcrumb" :key="item.id">
          <span v-if="i > 0" class="text-green-400 mx-1">/</span>
          <button
            class="text-green-700 hover:text-green-900 transition-colors duration-300"
            :class="
              i === store.breadcrumb.length - 1
                ? 'font-bold text-green-900'
                : ''
            "
            @click="store.navigateTo(item)"
          >
            {{ item.name }}
          </button>
        </template>
      </nav>

      <!-- Actions -->
      <div class="flex gap-2">
        <button
          class="px-4 py-2 rounded-2xl text-sm font-medium transition-all duration-300
                 border border-green-200 text-green-700 hover:bg-green-50 active:scale-95"
          @click="router.push('/tools/gy-netdisk')"
        >
          返回
        </button>
        <button
          class="px-4 py-2 rounded-2xl text-sm font-medium transition-all duration-300
                 border border-green-200 text-green-700 hover:bg-green-50 active:scale-95"
          @click="store.loadFiles(store.currentParentId)"
        >
          刷新
        </button>
        <button
          class="px-4 py-2 rounded-2xl text-sm font-medium transition-all duration-300
                 bg-green-500 text-white hover:bg-green-600 active:scale-95"
          @click="store.showCloudDialog = true"
        >
          云下载
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="text-center py-16">
      <div
        class="w-8 h-8 border-2 border-green-300 border-t-green-600 rounded-full animate-spin mx-auto mb-3"
      />
      <p class="text-green-600 text-sm">加载中...</p>
    </div>

    <!-- Empty -->
    <div
      v-else-if="store.files.length === 0"
      class="text-center py-16 text-green-500"
    >
      <p class="text-4xl mb-3">📂</p>
      <p>此文件夹为空</p>
    </div>

    <!-- File list -->
    <div v-else class="bg-white/80 border border-green-200 rounded-3xl overflow-hidden">
      <!-- Header -->
      <div
        class="hidden md:grid grid-cols-[1fr_80px_120px_140px_80px] gap-4 px-6 py-3
               border-b border-green-100 text-xs font-medium text-green-600 uppercase"
      >
        <span>文件名</span>
        <span>类型</span>
        <span>大小</span>
        <span>修改时间</span>
        <span>操作</span>
      </div>

      <!-- Rows -->
      <div
        v-for="file in store.files"
        :key="file.file_id"
        class="grid grid-cols-1 md:grid-cols-[1fr_80px_120px_140px_80px] gap-2 md:gap-4
               px-6 py-4 border-b border-green-50 last:border-b-0
               hover:bg-green-50/50 transition-colors duration-200"
      >
        <!-- Name -->
        <div class="flex items-center gap-3 min-w-0">
          <span class="text-xl flex-shrink-0">{{
            TYPE_ICONS[file.type] ?? TYPE_ICONS.file
          }}</span>
          <button
            v-if="file.type === 'folder'"
            class="text-left truncate text-green-900 hover:text-green-700
                   transition-colors duration-300 font-medium"
            @click="store.enterFolder(file.file_id, file.name)"
          >
            {{ file.name }}
          </button>
          <span v-else class="truncate text-green-900">{{ file.name }}</span>
        </div>

        <!-- Type -->
        <span class="text-sm text-green-600 hidden md:block">{{
          file.type
        }}</span>

        <!-- Size -->
        <span class="text-sm text-green-600 hidden md:block">
          {{ file.type === "folder" ? "-" : useFormatSize(file.size) }}
        </span>

        <!-- Time -->
        <span class="text-sm text-green-500 hidden md:block">
          {{ useRelativeTime(file.updated_at) }}
        </span>

        <!-- Actions -->
        <div class="hidden md:flex items-center">
          <button
            v-if="file.type !== 'folder'"
            class="text-sm text-green-600 hover:text-green-900
                   transition-colors duration-300"
            @click="handleDownload(file.file_id)"
          >
            下载
          </button>
        </div>

        <!-- Mobile meta -->
        <div class="flex items-center gap-3 text-xs text-green-500 md:hidden">
          <span>{{ file.type }}</span>
          <span v-if="file.type !== 'folder'">{{
            useFormatSize(file.size)
          }}</span>
          <span>{{ useRelativeTime(file.updated_at) }}</span>
          <button
            v-if="file.type !== 'folder'"
            class="ml-auto text-green-600 underline"
            @click="handleDownload(file.file_id)"
          >
            下载
          </button>
        </div>
      </div>
    </div>

    <!-- Cloud download dialog -->
    <div
      v-if="store.showCloudDialog"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm"
      @click.self="store.showCloudDialog = false"
    >
      <div
        class="w-full max-w-lg bg-white/95 border border-green-200 rounded-3xl p-6
               shadow-xl shadow-green-200/30 max-h-[80vh] overflow-y-auto"
      >
        <div class="flex items-center justify-between mb-5">
          <h2 class="font-bold text-xl text-green-900">云下载</h2>
          <button
            class="text-green-400 hover:text-green-700 transition-colors text-xl"
            @click="store.showCloudDialog = false"
          >
            ✕
          </button>
        </div>

        <!-- Default folder config -->
        <div class="flex items-center gap-2 mb-4 text-sm">
          <span class="text-green-600">下载到：</span>
          <template v-if="!editingFolder">
            <span class="text-green-900 font-medium">
              {{ store.cloudFolderId || "根目录" }}
            </span>
            <button
              class="text-green-500 hover:text-green-700 transition-colors"
              @click="folderInput = store.cloudFolderId; editingFolder = true"
            >
              修改
            </button>
          </template>
          <template v-else>
            <input
              v-model="folderInput"
              type="text"
              placeholder="文件夹 ID（留空 = 根目录）"
              class="flex-1 bg-white/80 border border-green-200 rounded-xl text-gray-800
                     focus:border-green-400 px-3 py-1.5 text-sm outline-none
                     transition-all duration-300"
            />
            <button
              class="px-3 py-1.5 rounded-xl text-xs font-medium
                     bg-green-500 text-white hover:bg-green-600 transition-all duration-300"
              @click="store.saveCloudFolder(folderInput.trim()); editingFolder = false"
            >
              保存
            </button>
            <button
              class="text-green-400 hover:text-green-600 text-xs transition-colors"
              @click="editingFolder = false"
            >
              取消
            </button>
          </template>
        </div>

        <!-- URL input -->
        <div class="mb-2">
          <textarea
            v-model="store.cloudUrl"
            rows="4"
            placeholder="输入下载链接（HTTP/magnet/ed2k），多个链接每行一个"
            class="w-full bg-white/80 border border-green-200 rounded-2xl text-gray-800
                   focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
                   px-4 py-3 text-sm outline-none transition-all duration-300 resize-y"
          />
        </div>
        <div class="flex items-center gap-3 mb-5">
          <span
            v-if="store.cloudUrl.trim().split('\n').filter(Boolean).length > 1"
            class="text-xs text-green-600"
          >
            检测到 {{ store.cloudUrl.trim().split("\n").filter(Boolean).length }} 个链接
          </span>
          <div class="flex-1" />
          <button
            class="px-5 py-2.5 rounded-2xl font-medium transition-all duration-300
                   bg-green-500 text-white hover:bg-green-600 active:scale-95
                   disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            :disabled="!store.cloudUrl.trim() || store.cloudLoading"
            @click="store.submitCloudDownload()"
          >
            {{ store.cloudLoading ? "提交中..." : "下载" }}
          </button>
        </div>

        <!-- Feedback message -->
        <div
          v-if="store.cloudMessage"
          class="mb-4 px-4 py-3 rounded-2xl text-sm border"
          :class="
            store.cloudMessage.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-700'
          "
        >
          {{ store.cloudMessage.text }}
        </div>

        <!-- Task list -->
        <div v-if="store.cloudTasks.length > 0">
          <h3 class="text-sm font-medium text-green-800 mb-3">下载任务</h3>
          <div class="space-y-2">
            <div
              v-for="task in store.cloudTasks"
              :key="task.taskId"
              class="flex items-center justify-between gap-3 p-3
                     bg-green-50/60 border border-green-100 rounded-2xl"
            >
              <div class="min-w-0 flex-1">
                <p class="text-sm text-green-900 truncate">
                  {{ task.fileName || task.url }}
                </p>
                <div class="flex items-center gap-2 mt-1">
                  <span
                    class="inline-block px-2 py-0.5 rounded-full text-xs border"
                    :class="
                      TASK_STATUS[task.status]?.color ??
                      'bg-gray-100 text-gray-600 border-gray-200'
                    "
                  >
                    {{ TASK_STATUS[task.status]?.label ?? "未知" }}
                  </span>
                  <span
                    v-if="task.fileSize"
                    class="text-xs text-green-500"
                  >
                    {{ useFormatSize(task.fileSize) }}
                  </span>
                </div>
              </div>
              <div class="flex gap-1 flex-shrink-0">
                <button
                  v-if="task.status === 5"
                  class="px-3 py-1.5 rounded-xl text-xs font-medium
                         border border-green-200 text-green-700
                         hover:bg-green-50 transition-all duration-300"
                  @click="store.retryTask(task.taskId)"
                >
                  重试
                </button>
                <button
                  class="px-3 py-1.5 rounded-xl text-xs font-medium
                         border border-red-200 text-red-600
                         hover:bg-red-50 transition-all duration-300"
                  @click="store.deleteTasks([task.taskId])"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-6 text-green-400 text-sm">
          暂无下载任务
        </div>
      </div>
    </div>
  </template>
</template>
