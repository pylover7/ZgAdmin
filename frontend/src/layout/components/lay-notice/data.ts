import { $t } from "@/plugins/i18n";

export interface ListItem {
  avatar: string;
  title: string;
  datetime: string;
  type: string;
  description: string;
  status?: "primary" | "success" | "warning" | "info" | "danger";
  extra?: string;
  /** 通知 ID，用于标记已读 */
  noticeId?: string;
}

export interface TabItem {
  key: string;
  name: string;
  list: ListItem[];
  emptyText: string;
}

/** 后端 /notice/unread 返回的单条通知 */
export interface ApiNotice {
  id: string;
  title: string;
  content: string;
  type: number; // 0-系统, 1-业务, 2-公告
  level: string; // info / warning / important
  status: number; // 1-已发布
  creator_id: string;
  created_at: string;
}

/** 后端 /notice/unread 返回结构 */
export interface UnreadResult {
  count: number;
  list: ApiNotice[];
}

/** level → el-tag type 映射 */
const levelMap: Record<
  string,
  "primary" | "success" | "warning" | "info" | "danger"
> = {
  info: "info",
  warning: "warning",
  important: "danger"
};

/** type 编号 → 中文名（用于 extra 标签） */
const typeLabel: Record<number, string> = {
  0: "系统",
  1: "业务",
  2: "公告"
};

/** 将后端通知转为前端展示格式 */
export function transformNotice(item: ApiNotice): ListItem {
  return {
    avatar: "",
    title: item.title,
    datetime: item.created_at,
    type: String(item.type),
    description: item.content,
    status: levelMap[item.level] || "info",
    extra: typeLabel[item.type] || "",
    noticeId: item.id
  };
}
