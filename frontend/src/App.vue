<script setup lang="ts">
import { RouterView } from "vue-router";
</script>

<template>
  <div class="min-h-screen bg-green-50">
    <nav class="bg-white/80 border-b border-green-200 px-4 md:px-8 py-3">
      <div class="max-w-6xl mx-auto flex items-center justify-between">
        <router-link
          to="/"
          class="font-bold text-xl md:text-2xl text-green-800"
        >
          P Tools
        </router-link>
        <div class="flex gap-4 md:gap-6 text-sm md:text-base" />
      </div>
    </nav>
    <main class="px-4 md:px-8 py-6 md:py-10">
      <div class="max-w-6xl mx-auto">
        <RouterView />
      </div>
    </main>
  </div>
</template>
