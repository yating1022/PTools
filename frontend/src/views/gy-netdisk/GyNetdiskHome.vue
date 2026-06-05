<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useGyNetdiskStore } from "@/stores/gyNetdisk";

const router = useRouter();
const store = useGyNetdiskStore();

const features = [
  {
    name: "文件管理",
    description: "浏览文件、云下载",
    route: "/tools/gy-netdisk/files",
    icon: "📁",
  },
  {
    name: "磁力管理",
    description: "导入、搜索、管理磁力链接",
    route: "/tools/gy-netdisk/magnets",
    icon: "🧲",
  },
  {
    name: "每日入库",
    description: "定时自动云下载磁力链接",
    route: "/tools/gy-netdisk/daily-import",
    icon: "⏰",
  },
];

onMounted(async () => {
  await store.checkAuth();
  if (!store.isAuthenticated) {
    router.replace("/tools/gy-netdisk/login");
  }
});
</script>

<template>
  <div v-if="!store.isAuthenticated" class="text-center py-20 text-green-600">
    检查登录状态中...
  </div>

  <div v-else>
    <h1 class="font-bold text-2xl md:text-3xl text-green-900 mb-2">光鸭网盘</h1>
    <p class="text-sm text-green-600 mb-8">
      已登录：<span class="font-medium text-green-800">{{ store.user?.phone || store.phone }}</span>
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
      <router-link
        v-for="f in features"
        :key="f.route"
        :to="f.route"
        class="block bg-white/80 border border-green-200 rounded-3xl p-6
               transition-all duration-300
               hover:shadow-xl hover:shadow-green-200/50 hover:-translate-y-1"
      >
        <span class="text-3xl mb-3 block">{{ f.icon }}</span>
        <h2 class="font-bold text-xl text-green-900 mb-1">{{ f.name }}</h2>
        <p class="text-sm text-green-700">{{ f.description }}</p>
      </router-link>
    </div>
  </div>
</template>
