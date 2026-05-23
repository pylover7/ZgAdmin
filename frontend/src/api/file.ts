import { http } from "@/utils/http";
import { apiV1 } from "@/api/utils";
import type { Result, ResultTable } from "@/types";

const fileUrl = (url: string) => apiV1(`/resource/file${url}`);

/** 上传单个文件 */
export const uploadFile = (formData: FormData) => {
  return http.request<Result>("post", fileUrl("/upload"), {
    data: formData,
    headers: { "Content-Type": "multipart/form-data" }
  });
};

/** 批量上传文件 */
export const uploadBatch = (formData: FormData) => {
  return http.request<Result>("post", fileUrl("/upload-batch"), {
    data: formData,
    headers: { "Content-Type": "multipart/form-data" }
  });
};

/** 文件列表 */
export const getFileList = (
  data?: object,
  currentPage?: number,
  pageSize?: number
) => {
  return http.request<ResultTable>("post", fileUrl("/list"), {
    data,
    params: { currentPage, pageSize }
  });
};

/** 重命名文件 */
export const updateFile = (data?: object) => {
  return http.request<Result>("post", fileUrl("/update"), { data });
};

/** 删除文件 */
export const deleteFile = (data?: string[]) => {
  return http.request<Result>("post", fileUrl("/delete"), { data });
};

/** 预览文件（返回 blob） */
export const previewFile = (fileId: string) => {
  return http.request<Blob>("get", fileUrl(`/preview/${fileId}`), {
    responseType: "blob"
  });
};

/** 获取下载签名 URL */
export const getSignedUrl = (fileId: string) => {
  return http.request<Result>("get", fileUrl(`/sign-url/${fileId}`));
};

/** 存储统计 */
export const getStorageStats = () => {
  return http.request<Result>("get", fileUrl("/stats"));
};
