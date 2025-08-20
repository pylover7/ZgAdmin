import { http } from "@/utils/http";
import { apiV1 } from "./utils";

const baseUrl = (url: string) => apiV1(`/base${url}`);

type Result = {
  success: boolean;
  data: Array<any>;
};

export const getAsyncRoutes = () => {
  return http.request<Result>("get", baseUrl("/userMenu"));
};
