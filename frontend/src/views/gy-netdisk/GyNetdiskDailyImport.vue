<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  type DailyImportConfig,
  type DailyImportStatus,
  getDailyImportConfig,
  getDailyImportStatus,
  saveDailyImportConfig,
  triggerDailyImport,
} from "@/api/modules/gyNetdisk";
import FolderPicker from "@/components/FolderPicker.vue";

const router = useRouter();

const config = ref<DailyImportConfig>({ hour: 3, count: 10, enabled: true, folder: "" });
const status = ref<DailyImportStatus | null>(null);
const loading = ref(false);
const saving = ref(false);
const running = ref(false);
const saveMsg = ref("");
const runMsg = ref("");
const runError = ref("");

const hours = Array.from({ length: 24 }, (_, i) => i);

async function load() {
  loading.value = true;
  try {
    const [cfg, st] = await Promise.all([
      getDailyImportConfig(),
      getDailyImportStatus(),
    ]);
    config.value = cfg;
    status.value = st;
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  saving.value = true;
  saveMsg.value = "";
  try {
    await saveDailyImportConfig(config.value.hour, config.value.count, config.value.enabled, config.value.folder);
    saveMsg.value = "保存成功";
    await load();
  } catch (e: any) {
    saveMsg.value = e?.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

async function handleRun() {
  running.value = true;
  runMsg.value = "";
  runError.value = "";
  try {
    const res = await triggerDailyImport();
    runMsg.value = res.message;
    await load();
  } catch (e: any) {
    runError.value = e?.message || "执行失败";
  } finally {
    running.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="font-bold text-2xl md:text-3xl text-green-900">每日入库</h1>
      <button
        class="px-4 py-2 rounded-2xl text-sm font-medium border border-green-200
               text-green-700 hover:bg-green-50 transition-all duration-300"
        @click="router.push('/tools/gy-netdisk')"
      >
        返回网盘
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="w-8 h-8 border-2 border-green-300 border-t-green-600 rounded-full animate-spin mx-auto mb-3" />
      <p class="text-green-600 text-sm">加载中...</p>
    </div>

    <template v-else>
      <!-- Config Card -->
      <div class="bg-white/80 border border-green-200 rounded-3xl p-5 mb-6">
        <h2 class="font-medium text-green-900 mb-4">定时配置</h2>
        <div class="flex flex-wrap items-end gap-4">
          <!-- Enabled toggle -->
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              v-model="config.enabled"
              type="checkbox"
              class="w-4 h-4 accent-green-600"
            />
            <span class="text-sm text-green-800">启用定时任务</span>
          </label>

          <!-- Hour -->
          <div>
            <label class="block text-xs text-green-600 mb-1">执行时间（小时）</label>
            <select
              v-model.number="config.hour"
              class="bg-white border border-green-200 rounded-xl px-3 py-2 text-sm text-green-900
                     focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
                     outline-none transition-all duration-300"
            >
              <option v-for="h in hours" :key="h" :value="h">
                {{ String(h).padStart(2, "0") }}:00
              </option>
            </select>
          </div>

          <!-- Count -->
          <div>
            <label class="block text-xs text-green-600 mb-1">每次下载条数</label>
            <input
              v-model.number="config.count"
              type="number"
              min="1"
              class="w-24 bg-white border border-green-200 rounded-xl px-3 py-2 text-sm text-green-900
                     focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
                     outline-none transition-all duration-300"
            />
          </div>

          <!-- Folder -->
          <div class="w-full">
            <label class="block text-xs text-green-600 mb-1">下载目录</label>
            <FolderPicker v-model="config.folder" />
          </div>

          <!-- Save -->
          <button
            class="px-5 py-2 rounded-2xl text-sm font-medium transition-all duration-300
                   bg-green-500 text-white hover:bg-green-600 active:scale-95
                   disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="saving"
            @click="handleSave"
          >
            {{ saving ? "保存中..." : "保存配置" }}
          </button>

          <span v-if="saveMsg" class="text-sm text-green-600">{{ saveMsg }}</span>
        </div>
      </div>

      <!-- Status Card -->
      <div class="bg-white/80 border border-green-200 rounded-3xl p-5 mb-6">
        <h2 class="font-medium text-green-900 mb-4">状态概览</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-green-900">{{ status?.total_undownloaded ?? 0 }}</p>
            <p class="text-xs text-green-600">待下载</p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-green-900">{{ status?.total_downloaded ?? 0 }}</p>
            <p class="text-xs text-green-600">已下载</p>
          </div>
          <div class="text-center">
            <p class="text-sm font-medium text-green-900">
              {{ status?.enabled ? status?.next_run || "-" : "未启用" }}
            </p>
            <p class="text-xs text-green-600">下次执行</p>
          </div>
          <div class="text-center">
            <p class="text-sm font-medium text-green-900">
              {{ status?.last_run_time || "-" }}
            </p>
            <p class="text-xs text-green-600">上次执行</p>
          </div>
        </div>

        <!-- Manual trigger -->
        <div class="flex items-center gap-3 pt-3 border-t border-green-100">
          <button
            class="px-5 py-2 rounded-2xl text-sm font-medium transition-all duration-300
                   bg-green-500 text-white hover:bg-green-600 active:scale-95
                   disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="running || status?.is_running"
            @click="handleRun"
          >
            {{ running || status?.is_running ? "执行中..." : "立即执行一次" }}
          </button>
          <span v-if="runMsg" class="text-sm text-green-600">{{ runMsg }}</span>
          <span v-if="runError" class="text-sm text-red-600">{{ runError }}</span>
        </div>
      </div>

      <!-- Last run results -->
      <div
        v-if="status?.last_run_results?.length"
        class="bg-white/80 border border-green-200 rounded-3xl p-5"
      >
        <h2 class="font-medium text-green-900 mb-3">上次执行详情</h2>
        <p class="text-xs text-green-500 mb-3">{{ status?.last_run_time }}</p>
        <div class="space-y-2 max-h-[400px] overflow-y-auto">
          <div
            v-for="(r, i) in status?.last_run_results"
            :key="i"
            class="flex items-center gap-3 px-4 py-2 rounded-xl text-sm"
            :class="
              r.status === 'ok'
                ? 'bg-green-50 text-green-800'
                : 'bg-red-50 text-red-700'
            "
          >
            <span class="font-mono font-medium flex-1">{{ r.bangou }}</span>
            <span v-if="r.status === 'ok'" class="text-green-600">成功</span>
            <span v-else class="text-red-500 text-xs truncate max-w-[200px]" :title="r.detail">
              失败: {{ r.detail }}
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
