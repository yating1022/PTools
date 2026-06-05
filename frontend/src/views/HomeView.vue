<script setup lang="ts">
const tools = [
  {
    name: "光鸭网盘",
    description: "文件管理、云下载、磁力链接",
    route: "/tools/gy-netdisk",
    icon: "🦆",
  },
];
</script>

<template>
  <div>
    <h1 class="font-bold text-3xl md:text-5xl text-green-900 mb-8 md:mb-12">
      P Tools
    </h1>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
      <router-link
        v-for="tool in tools"
        :key="tool.route"
        :to="tool.route"
        class="block bg-white/80 border border-green-200 rounded-3xl p-6
               transition-all duration-300
               hover:shadow-xl hover:shadow-green-200/50 hover:-translate-y-1"
      >
        <span class="text-3xl mb-3 block">{{ tool.icon }}</span>
        <h2 class="font-bold text-xl md:text-2xl text-green-900 mb-2">
          {{ tool.name }}
        </h2>
        <p class="text-sm md:text-base text-green-700">
          {{ tool.description }}
        </p>
      </router-link>
    </div>
  </div>
</template>
