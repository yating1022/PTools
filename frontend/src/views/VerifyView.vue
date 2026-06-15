<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const router = useRouter();
const secretKey = ref("");
const loading = ref(false);
const error = ref("");

async function handleVerify() {
  if (!secretKey.value.trim()) return;
  loading.value = true;
  error.value = "";
  try {
    const res: any = await api.post("/verify", {
      secret_key: secretKey.value.trim(),
    });
    localStorage.setItem("p_token", res.token);
    router.replace("/");
  } catch (e: any) {
    error.value = e?.message || "验证失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div
      class="w-full max-w-sm bg-white/80 border border-green-200 rounded-3xl p-8
             shadow-xl shadow-green-200/20"
    >
      <div class="text-center mb-6">
        <span class="text-4xl block mb-3">🔐</span>
        <h1 class="font-bold text-2xl text-green-900">访问验证</h1>
        <p class="text-sm text-green-600 mt-1">请输入访问密钥以继续</p>
      </div>

      <form @submit.prevent="handleVerify">
        <input
          v-model="secretKey"
          type="password"
          placeholder="输入访问密钥"
          autofocus
          class="w-full bg-white/80 border border-green-200 rounded-2xl text-gray-800
                 focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
                 px-4 py-3 text-sm outline-none transition-all duration-300 mb-4"
        />
        <button
          type="submit"
          class="w-full px-5 py-3 rounded-2xl font-medium transition-all duration-300
                 bg-green-500 text-white hover:bg-green-600 active:scale-95
                 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          :disabled="!secretKey.trim() || loading"
        >
          {{ loading ? "验证中..." : "验证" }}
        </button>
      </form>

      <p v-if="error" class="mt-4 text-center text-sm text-red-600">{{ error }}</p>
    </div>
  </div>
</template>
