import { reactive } from "vue";
import type { FormRules } from "element-plus";
import { transformI18n } from "@/plugins/i18n";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
  title: [
    {
      required: true,
      message: transformI18n("system.menu.titleRequired"),
      trigger: "blur"
    }
  ],
  name: [
    {
      required: true,
      message: transformI18n("system.menu.routeNameRequired"),
      trigger: "blur"
    }
  ],
  path: [
    {
      required: true,
      message: transformI18n("system.menu.routePathRequired"),
      trigger: "blur"
    }
  ],
  auths: [
    {
      required: true,
      message: transformI18n("system.menu.authRequired"),
      trigger: "blur"
    }
  ]
});
