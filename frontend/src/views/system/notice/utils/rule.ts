import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
  title: [{ required: true, message: "通知标题为必填项", trigger: "blur" }],
  type: [{ required: true, message: "请选择通知类型", trigger: "change" }],
  level: [{ required: true, message: "请选择通知级别", trigger: "change" }]
});
