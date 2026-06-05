import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
    },
    {
      path: "/tools/gy-netdisk",
      name: "gy-netdisk-home",
      component: () => import("@/views/gy-netdisk/GyNetdiskHome.vue"),
    },
    {
      path: "/tools/gy-netdisk/files",
      name: "gy-netdisk-files",
      component: () => import("@/views/gy-netdisk/GyNetdiskFiles.vue"),
    },
    {
      path: "/tools/gy-netdisk/login",
      name: "gy-netdisk-login",
      component: () => import("@/views/gy-netdisk/GyNetdiskLogin.vue"),
    },
    {
      path: "/tools/gy-netdisk/magnets",
      name: "gy-netdisk-magnets",
      component: () => import("@/views/gy-netdisk/GyNetdiskMagnets.vue"),
    },
    {
      path: "/tools/gy-netdisk/daily-import",
      name: "gy-netdisk-daily-import",
      component: () => import("@/views/gy-netdisk/GyNetdiskDailyImport.vue"),
    },
  ],
});

export default router;
