import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { Result, ResultTable } from "@/types";

const noticeUrl = (url: string) => apiV1(`/system/notice${url}`);

/** 发布通知 */
export const addNotice = (data?: object) => {
  return http.request<Result>("post", noticeUrl("/add"), { data });
};

/** 通知列表 */
export const getNoticeList = (
  title: string,
  type: number | null,
  level: string,
  status: number | null,
  currentPage: number,
  pageSize: number
) => {
  return http.request<ResultTable>("post", noticeUrl("/list"), {
    data: { title, type, level, status },
    params: { pageSize, currentPage }
  });
};

/** 编辑通知 */
export const updateNotice = (data?: object) => {
  return http.request<Result>("post", noticeUrl("/update"), { data });
};

/** 删除通知 */
export const deleteNotice = (data?: string[]) => {
  return http.request<Result>("post", noticeUrl("/delete"), { data });
};

/** 获取未读通知 */
export const getUnreadNotices = () => {
  return http.request<Result>("get", noticeUrl("/unread"));
};

/** 标记单条已读 */
export const markNoticeRead = (notice_id: string) => {
  return http.request<Result>("post", noticeUrl("/read"), {
    data: { notice_id }
  });
};

/** 全部标记已读 */
export const markAllRead = () => {
  return http.request<Result>("post", noticeUrl("/readAll"));
};
