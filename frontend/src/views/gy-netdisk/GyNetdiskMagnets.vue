<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  type MagnetItem,
  deleteMagnets,
  importMagnets,
  listMagnets,
} from "@/api/modules/gyNetdisk";

const router = useRouter();

// ── State ───────────────────────────────────────────────
const items = ref<MagnetItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const keyword = ref("");
const loading = ref(false);

const fileInput = ref<HTMLInputElement | null>(null);
const importing = ref(false);
const importResult = ref<{ imported: number; skipped: number; total: number } | null>(null);
const importError = ref("");

const selectedIds = ref<number[]>([]);

// ── Actions ─────────────────────────────────────────────
async function load() {
  loading.value = true;
  try {
    const res = await listMagnets({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    });
    items.value = res.items;
    total.value = res.total;
  } finally {
    loading.value = false;
  }
}

function search() {
  page.value = 1;
  load();
}

function goPage(p: number) {
  page.value = p;
  load();
}

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize.value));

async function handleImport() {
  const file = fileInput.value?.files?.[0];
  if (!file) return;
  importing.value = true;
  importResult.value = null;
  importError.value = "";
  try {
    importResult.value = await importMagnets(file);
    page.value = 1;
    await load();
  } catch (e: any) {
    importError.value = e?.response?.data?.detail || e.message || "导入失败";
  } finally {
    importing.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

function toggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id);
  if (idx >= 0) selectedIds.value.splice(idx, 1);
  else selectedIds.value.push(id);
}

function toggleAll() {
  if (selectedIds.value.length === items.value.length) {
    selectedIds.value = [];
  } else {
    selectedIds.value = items.value.map((i) => i.id);
  }
}

async function handleDelete() {
  if (!selectedIds.value.length) return;
  if (!confirm(`确定删除 ${selectedIds.value.length} 条记录？`)) return;
  await deleteMagnets(selectedIds.value);
  selectedIds.value = [];
  await load();
}

function copyMagnet(magnet: string) {
  navigator.clipboard.writeText(magnet);
}

onMounted(load);
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="font-bold text-2xl md:text-3xl text-green-900">磁力链接管理</h1>
      <button
        class="px-4 py-2 rounded-2xl text-sm font-medium border border-green-200
               text-green-700 hover:bg-green-50 transition-all duration-300"
        @click="router.push('/tools/gy-netdisk')"
      >
        返回网盘
      </button>
    </div>

    <!-- Import section -->
    <div class="bg-white/80 border border-green-200 rounded-3xl p-5 mb-6">
      <h2 class="font-medium text-green-900 mb-3">导入 Excel / CSV</h2>
      <p class="text-xs text-green-600 mb-3">
        格式要求：第一行为表头，A列=番号，B列=标题，C列=磁力链接（支持 .xlsx / .xls / .csv）
      </p>
      <div class="flex items-center gap-3 flex-wrap">
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.xls,.csv,.tsv"
          class="text-sm text-green-700 file:mr-3 file:py-2 file:px-4
                 file:rounded-xl file:border-0 file:text-sm file:font-medium
                 file:bg-green-100 file:text-green-800 hover:file:bg-green-200
                 file:transition-colors file:duration-300"
        />
        <button
          class="px-5 py-2 rounded-2xl text-sm font-medium transition-all duration-300
                 bg-green-500 text-white hover:bg-green-600 active:scale-95
                 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="importing"
          @click="handleImport"
        >
          {{ importing ? "导入中..." : "开始导入" }}
        </button>
      </div>
      <div
        v-if="importResult"
        class="mt-3 px-4 py-3 rounded-2xl text-sm bg-green-50 border border-green-200 text-green-800"
      >
        导入完成：新增 {{ importResult.imported }} 条，跳过（已存在）{{ importResult.skipped }} 条，共 {{ importResult.total }} 条
      </div>
      <div
        v-if="importError"
        class="mt-3 px-4 py-3 rounded-2xl text-sm bg-red-50 border border-red-200 text-red-700"
      >
        {{ importError }}
      </div>
    </div>

    <!-- Search + Actions -->
    <div class="flex items-center gap-3 mb-4 flex-wrap">
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索番号或标题..."
        class="flex-1 min-w-[200px] bg-white/80 border border-green-200 rounded-2xl text-gray-800
               focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
               px-4 py-2.5 text-sm outline-none transition-all duration-300"
        @keyup.enter="search"
      />
      <button
        class="px-5 py-2.5 rounded-2xl text-sm font-medium border border-green-200
               text-green-700 hover:bg-green-50 transition-all duration-300"
        @click="search"
      >
        搜索
      </button>
      <button
        v-if="selectedIds.length > 0"
        class="px-4 py-2.5 rounded-2xl text-sm font-medium border border-red-200
               text-red-600 hover:bg-red-50 transition-all duration-300"
        @click="handleDelete"
      >
        删除选中 ({{ selectedIds.length }})
      </button>
      <span class="text-sm text-green-500 ml-auto">共 {{ total }} 条</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="w-8 h-8 border-2 border-green-300 border-t-green-600 rounded-full animate-spin mx-auto mb-3" />
      <p class="text-green-600 text-sm">加载中...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="items.length === 0" class="text-center py-12 text-green-500">
      <p class="text-4xl mb-3">🧲</p>
      <p>暂无磁力链接数据，请先导入 Excel</p>
    </div>

    <!-- Table -->
    <div v-else class="bg-white/80 border border-green-200 rounded-3xl overflow-hidden">
      <!-- Header -->
      <div
        class="hidden md:grid grid-cols-[40px_100px_1fr_120px_80px] gap-4 px-6 py-3
               border-b border-green-100 text-xs font-medium text-green-600 uppercase"
      >
        <span>
          <input
            type="checkbox"
            :checked="selectedIds.length === items.length && items.length > 0"
            @change="toggleAll"
          />
        </span>
        <span>番号</span>
        <span>标题</span>
        <span>磁力链接</span>
        <span>操作</span>
      </div>

      <!-- Rows -->
      <div
        v-for="item in items"
        :key="item.id"
        class="grid grid-cols-1 md:grid-cols-[40px_100px_1fr_120px_80px] gap-2 md:gap-4
               px-6 py-4 border-b border-green-50 last:border-b-0
               hover:bg-green-50/50 transition-colors duration-200"
      >
        <!-- Checkbox -->
        <div class="hidden md:flex items-center">
          <input
            type="checkbox"
            :checked="selectedIds.includes(item.id)"
            @change="toggleSelect(item.id)"
          />
        </div>

        <!-- 番号 -->
        <div class="font-mono text-sm text-green-900 font-medium">
          {{ item.bangou }}
        </div>

        <!-- 标题 -->
        <div class="text-sm text-green-800 truncate" :title="item.title">
          {{ item.title }}
        </div>

        <!-- 磁力链接 -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-green-500 truncate max-w-[100px]" :title="item.magnet">
            {{ item.magnet.substring(0, 20) }}...
          </span>
          <button
            class="text-xs text-green-600 hover:text-green-900 transition-colors flex-shrink-0"
            @click="copyMagnet(item.magnet)"
          >
            复制
          </button>
        </div>

        <!-- 操作 -->
        <div class="flex items-center">
          <button
            class="text-xs text-red-500 hover:text-red-700 transition-colors"
            @click="selectedIds = [item.id]; handleDelete()"
          >
            删除
          </button>
        </div>

        <!-- Mobile -->
        <div class="flex items-center gap-3 text-xs text-green-500 md:hidden flex-wrap">
          <span class="font-mono font-medium text-green-900">{{ item.bangou }}</span>
          <span class="truncate flex-1">{{ item.title }}</span>
          <button class="text-green-600 underline" @click="copyMagnet(item.magnet)">复制链接</button>
          <button class="text-red-500" @click="selectedIds = [item.id]; handleDelete()">删除</button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages() > 1" class="flex items-center justify-center gap-2 mt-6">
      <button
        class="px-3 py-1.5 rounded-xl text-sm border border-green-200 text-green-700
               hover:bg-green-50 disabled:opacity-40 transition-all duration-300"
        :disabled="page <= 1"
        @click="goPage(page - 1)"
      >
        上一页
      </button>
      <span class="text-sm text-green-600">{{ page }} / {{ totalPages() }}</span>
      <button
        class="px-3 py-1.5 rounded-xl text-sm border border-green-200 text-green-700
               hover:bg-green-50 disabled:opacity-40 transition-all duration-300"
        :disabled="page >= totalPages()"
        @click="goPage(page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>
