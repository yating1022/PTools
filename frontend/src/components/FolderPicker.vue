<script setup lang="ts">
import { ref, watch } from "vue";
import { listFiles } from "@/api/modules/gyNetdisk";
import type { GyFile } from "@/types/gyNetdisk";

const props = defineProps<{ modelValue: string }>();
const emit = defineEmits<{ (e: "update:modelValue", v: string): void }>();

const show = ref(false);
const loading = ref(false);
const folders = ref<GyFile[]>([]);
const currentId = ref("");
const currentName = ref("根目录");
const breadcrumb = ref<{ id: string; name: string }[]>([
  { id: "", name: "根目录" },
]);

async function loadFolders(parentId = "") {
  loading.value = true;
  try {
    const res = await listFiles(parentId, "folder");
    folders.value = res.files.filter((f) => f.type === "folder");
    currentId.value = parentId;
  } finally {
    loading.value = false;
  }
}

function open() {
  show.value = true;
  breadcrumb.value = [{ id: "", name: "根目录" }];
  currentName.value = "根目录";
  loadFolders("");
}

function enterFolder(folderId: string, folderName: string) {
  breadcrumb.value.push({ id: folderId, name: folderName });
  currentName.value = folderName;
  loadFolders(folderId);
}

function navigateTo(idx: number) {
  const item = breadcrumb.value[idx];
  breadcrumb.value = breadcrumb.value.slice(0, idx + 1);
  currentName.value = item.name;
  loadFolders(item.id);
}

function selectCurrent() {
  emit("update:modelValue", currentId.value);
  show.value = false;
}

function clearSelection() {
  emit("update:modelValue", "");
  show.value = false;
}
</script>

<template>
  <div>
    <!-- 触发按钮 -->
    <div class="flex items-center gap-2">
      <button
        class="px-4 py-2 rounded-2xl text-sm font-medium transition-all duration-300
               border border-green-200 text-green-700 hover:bg-green-50"
        @click="open"
      >
        {{ modelValue ? "更换目录" : "选择目录" }}
      </button>
      <span v-if="modelValue" class="text-sm text-green-800 font-mono">
        {{ modelValue }}
      </span>
      <span v-else class="text-xs text-green-500">默认目录</span>
      <button
        v-if="modelValue"
        class="text-xs text-red-500 hover:text-red-700 transition-colors"
        @click="clearSelection"
      >
        清除
      </button>
    </div>

    <!-- 弹窗 -->
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm"
      @click.self="show = false"
    >
      <div
        class="w-full max-w-md bg-white/95 border border-green-200 rounded-3xl p-6
               shadow-xl shadow-green-200/30 max-h-[70vh] flex flex-col"
      >
        <!-- 标题 -->
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-bold text-lg text-green-900">选择下载目录</h2>
          <button
            class="text-green-400 hover:text-green-700 transition-colors text-xl"
            @click="show = false"
          >
            ✕
          </button>
        </div>

        <!-- 面包屑 -->
        <nav class="flex items-center gap-1 text-sm mb-3 flex-wrap">
          <template v-for="(item, i) in breadcrumb" :key="item.id + i">
            <span v-if="i > 0" class="text-green-400">/</span>
            <button
              class="hover:text-green-900 transition-colors"
              :class="i === breadcrumb.length - 1 ? 'font-bold text-green-900' : 'text-green-600'"
              @click="navigateTo(i)"
            >
              {{ item.name }}
            </button>
          </template>
        </nav>

        <!-- 选择当前目录 -->
        <button
          class="mb-3 w-full px-4 py-2.5 rounded-2xl text-sm font-medium transition-all duration-300
                 bg-green-500 text-white hover:bg-green-600 active:scale-95"
          @click="selectCurrent"
        >
          选择「{{ currentName }}」
        </button>

        <!-- 文件夹列表 -->
        <div class="flex-1 overflow-y-auto min-h-0">
          <div v-if="loading" class="text-center py-8">
            <div class="w-6 h-6 border-2 border-green-300 border-t-green-600 rounded-full animate-spin mx-auto" />
          </div>
          <div v-else-if="folders.length === 0" class="text-center py-8 text-green-400 text-sm">
            此目录下没有子文件夹
          </div>
          <div v-else class="space-y-1">
            <button
              v-for="folder in folders"
              :key="folder.file_id"
              class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-left
                     hover:bg-green-50 transition-colors duration-200"
              @click="enterFolder(folder.file_id, folder.name)"
            >
              <span class="text-lg">📁</span>
              <span class="text-green-900 truncate flex-1">{{ folder.name }}</span>
              <span class="text-green-400 text-xs flex-shrink-0">进入 →</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
