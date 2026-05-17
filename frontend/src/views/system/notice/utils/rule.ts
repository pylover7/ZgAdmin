import type { FormRules } from "element-plus";
import { transformI18n } from "@/plugins/i18n";

/** 自定义表单规则校验 */
export function useFormRules(): FormRules {
  return {
    title: [
      {
        required: true,
        message: transformI18n("system.notice.titleRequired"),
        trigger: "blur"
      }
    ],
    type: [
      {
        required: true,
        message: transformI18n("system.notice.typeRequired"),
        trigger: "change"
      }
    ],
    level: [
      {
        required: true,
        message: transformI18n("system.notice.levelRequired"),
        trigger: "change"
      }
    ]
  };
}
