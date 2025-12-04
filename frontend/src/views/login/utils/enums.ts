import { $t } from "@/plugins/i18n";
import QQ from "~icons/ri/qq-fill";
import WeChat from "~icons/ri/wechat-fill";

const operates = [
  {
    title: $t("login.QQLogin"),
    icon: QQ
  },
  {
    title: $t("login.WeChatLogin"),
    icon: WeChat
  }
];

export { operates };
