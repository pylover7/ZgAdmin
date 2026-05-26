import { reactive } from "vue";
import type { FormRules } from "element-plus";
import { isPhone, isEmail } from "@pureadmin/utils";
import { transformI18n } from "@/plugins/i18n";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
  nickname: [
    {
      required: true,
      message: transformI18n("system.nicknameRequired"),
      trigger: "blur"
    }
  ],
  username: [
    {
      required: true,
      message: transformI18n("system.usernameRequired"),
      trigger: "blur"
    }
  ],
  password: [
    {
      required: true,
      message: transformI18n("system.passwordRequired"),
      trigger: "blur"
    }
  ],
  phone: [
    {
      validator: (rule, value, callback) => {
        if (value === "") {
          callback();
        } else if (!isPhone(value)) {
          callback(new Error(transformI18n("system.phoneFormatError")));
        } else {
          callback();
        }
      },
      trigger: "blur"
      // trigger: "click" // 如果想在点击确定按钮时触发这个校验，trigger 设置成 click 即可
    },
    {
      required: false,
      message: transformI18n("system.phoneInputRequired"),
      trigger: "blur"
    }
  ],
  email: [
    {
      required: true,
      message: transformI18n("system.emailInputRequired"),
      trigger: "blur"
    },
    {
      validator: (rule, value, callback) => {
        if (value === "") {
          callback();
        } else if (!isEmail(value)) {
          callback(new Error(transformI18n("system.emailFormatError")));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
});
