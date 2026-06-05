<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useGyNetdiskStore } from "@/stores/gyNetdisk";

const router = useRouter();
const store = useGyNetdiskStore();

const phoneInput = ref("+86");
const codeInput = ref("");
const verificationToken = ref("");
const error = ref("");
const sending = ref(false);
const countdown = ref(0);
let timer: ReturnType<typeof setInterval> | null = null;

async function handleInit() {
  error.value = "";
  try {
    await store.initLogin(phoneInput.value.trim());
    await handleSend();
  } catch (e: any) {
    error.value = e.message;
  }
}

async function handleSend() {
  error.value = "";
  sending.value = true;
  try {
    await store.sendCode();
    startCountdown();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    sending.value = false;
  }
}

function startCountdown() {
  countdown.value = 60;
  if (timer) clearInterval(timer);
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0 && timer) {
      clearInterval(timer);
      timer = null;
    }
  }, 1000);
}

async function handleVerify() {
  error.value = "";
  try {
    const res = await store.verifyCode(codeInput.value.trim());
    verificationToken.value = res.verification_token ?? "";
    await handleSignin();
  } catch (e: any) {
    error.value = e.message;
  }
}

async function handleSignin() {
  error.value = "";
  try {
    await store.completeLogin(codeInput.value.trim(), verificationToken.value);
    router.push("/tools/gy-netdisk");
  } catch (e: any) {
    error.value = e.message;
  }
}

const steps = [
  { num: 1, label: "输入手机号" },
  { num: 2, label: "发送验证码" },
  { num: 3, label: "输入验证码" },
  { num: 4, label: "完成登录" },
];
</script>

<template>
  <div class="max-w-md mx-auto">
    <h1 class="font-bold text-2xl md:text-3xl text-green-900 mb-8 text-center">
      光鸭网盘登录
    </h1>

    <!-- Steps indicator -->
    <div class="flex items-center justify-center gap-2 mb-8">
      <div
        v-for="step in steps"
        :key="step.num"
        class="flex items-center gap-2"
      >
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300"
          :class="
            store.authStep >= step.num
              ? 'bg-green-500 text-white'
              : 'bg-white/80 border border-green-200 text-green-400'
          "
        >
          {{ step.num }}
        </div>
        <span
          class="text-xs md:text-sm hidden sm:inline"
          :class="
            store.authStep >= step.num ? 'text-green-800' : 'text-green-400'
          "
        >
          {{ step.label }}
        </span>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="bg-red-50 border border-red-200 rounded-2xl p-4 mb-4 text-red-700 text-sm"
    >
      {{ error }}
    </div>

    <!-- Step 1: phone -->
    <div
      v-if="store.authStep === 1"
      class="bg-white/80 border border-green-200 rounded-3xl p-6"
    >
      <label class="block text-sm font-medium text-green-800 mb-2"
        >手机号</label
      >
      <input
        v-model="phoneInput"
        type="tel"
        placeholder="+8613800138000"
        class="w-full bg-white/80 border border-green-200 rounded-2xl text-gray-800
               focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
               px-4 py-3 mb-4 outline-none transition-all duration-300"
      />
      <button
        class="w-full px-6 py-3 rounded-2xl font-medium transition-all duration-300
               bg-green-500 text-white hover:bg-green-600 active:scale-95
               disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="!phoneInput.trim()"
        @click="handleInit"
      >
        下一步
      </button>
      <p class="text-xs text-green-500 mt-3 text-center">
        请带国际区号，如 +86 13800138000
      </p>
    </div>

    <!-- Step 2+3: code input -->
    <div
      v-if="store.authStep >= 2 && store.authStep <= 3"
      class="bg-white/80 border border-green-200 rounded-3xl p-6"
    >
      <p class="text-sm text-green-700 mb-4">
        验证码已发送至
        <span class="font-medium text-green-900">{{ store.phone }}</span>
      </p>
      <label class="block text-sm font-medium text-green-800 mb-2"
        >验证码</label
      >
      <input
        v-model="codeInput"
        type="text"
        maxlength="6"
        placeholder="输入 6 位验证码"
        class="w-full bg-white/80 border border-green-200 rounded-2xl text-gray-800
               focus:border-green-400 focus:shadow-lg focus:shadow-green-200/40
               px-4 py-3 mb-4 outline-none transition-all duration-300 tracking-[0.5em]"
      />
      <div class="flex gap-3">
        <button
          class="flex-1 px-6 py-3 rounded-2xl font-medium transition-all duration-300
                 border border-green-200 text-green-700 hover:bg-green-50 active:scale-95
                 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="countdown > 0 || sending"
          @click="handleSend"
        >
          {{ countdown > 0 ? `${countdown}s` : "重新发送" }}
        </button>
        <button
          class="flex-1 px-6 py-3 rounded-2xl font-medium transition-all duration-300
                 bg-green-500 text-white hover:bg-green-600 active:scale-95
                 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!codeInput.trim()"
          @click="handleVerify"
        >
          验证
        </button>
      </div>
    </div>

    <!-- Step 4: loading -->
    <div
      v-if="store.authStep === 4"
      class="bg-white/80 border border-green-200 rounded-3xl p-6 text-center"
    >
      <div
        class="w-8 h-8 border-2 border-green-300 border-t-green-600 rounded-full animate-spin mx-auto mb-4"
      />
      <p class="text-green-800">正在完成登录...</p>
    </div>
  </div>
</template>
