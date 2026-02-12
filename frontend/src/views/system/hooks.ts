// 抽离可公用的工具函数等用于系统管理页面逻辑
import dayjs from "dayjs";
import { computed } from "vue";
import { useDark } from "@pureadmin/utils";

/** 日志等级中文映射 */
export const levelTextMap: Record<string, string> = {
  info: "信息",
  warning: "警告",
  error: "重要"
};

/** 将日期时间范围转换为本地时间格式，避免时区偏移问题 */
export function formatDateTimeRange(
  timeRange: [Date, Date] | null
): [string, string] | null {
  if (!timeRange || timeRange.length !== 2) return null;
  return timeRange.map(date => dayjs(date).format("YYYY-MM-DDTHH:mm:ss")) as [
    string,
    string
  ];
}

export function usePublicHooks() {
  const { isDark } = useDark();

  const switchStyle = computed(() => {
    return {
      "--el-switch-on-color": "#6abe39",
      "--el-switch-off-color": "#e84749"
    };
  });

  const tagStyle = computed(() => {
    return (status: number) => {
      return status === 1
        ? {
            "--el-tag-text-color": isDark.value ? "#6abe39" : "#389e0d",
            "--el-tag-bg-color": isDark.value ? "#172412" : "#f6ffed",
            "--el-tag-border-color": isDark.value ? "#274a17" : "#b7eb8f"
          }
        : {
            "--el-tag-text-color": isDark.value ? "#e84749" : "#cf1322",
            "--el-tag-bg-color": isDark.value ? "#2b1316" : "#fff1f0",
            "--el-tag-border-color": isDark.value ? "#58191c" : "#ffa39e"
          };
    };
  });

  /** 日志等级标签样式 */
  const levelTagStyle = computed(() => {
    return (level: string) => {
      const styles: Record<string, Record<string, string>> = {
        info: isDark.value
          ? {
              "--el-tag-text-color": "#409eff",
              "--el-tag-bg-color": "#141414",
              "--el-tag-border-color": "#1a3a5c"
            }
          : {
              "--el-tag-text-color": "#1890ff",
              "--el-tag-bg-color": "#e6f7ff",
              "--el-tag-border-color": "#91d5ff"
            },
        warning: isDark.value
          ? {
              "--el-tag-text-color": "#faad14",
              "--el-tag-bg-color": "#2b2111",
              "--el-tag-border-color": "#594214"
            }
          : {
              "--el-tag-text-color": "#d48806",
              "--el-tag-bg-color": "#fffbe6",
              "--el-tag-border-color": "#ffe58f"
            },
        error: isDark.value
          ? {
              "--el-tag-text-color": "#ff4d4f",
              "--el-tag-bg-color": "#2b1316",
              "--el-tag-border-color": "#58191c"
            }
          : {
              "--el-tag-text-color": "#cf1322",
              "--el-tag-bg-color": "#fff1f0",
              "--el-tag-border-color": "#ffa39e"
            }
      };
      return styles[level] || styles.info;
    };
  });

  return {
    /** 当前网页是否为`dark`模式 */
    isDark,
    /** 表现更鲜明的`el-switch`组件  */
    switchStyle,
    /** 表现更鲜明的`el-tag`组件  */
    tagStyle,
    /** 日志等级标签样式 */
    levelTagStyle
  };
}
