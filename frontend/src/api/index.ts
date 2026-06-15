import axios from "axios";
import router from "@/router";

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("p_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("p_token");
      router.replace("/verify");
    }
    const msg = err.response?.data?.detail ?? err.message;
    return Promise.reject(new Error(msg));
  },
);

export default api;
