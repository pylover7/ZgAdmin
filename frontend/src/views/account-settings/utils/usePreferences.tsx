import { ref, onMounted } from "vue";
import { message } from "@/utils/message";
import { getPreferences, updatePreferences } from "@/api/user";
import { transformI18n } from "@/plugins/i18n";

export function usePreferences() {
  const list = ref([
    {
      key: "notify_account",
      title: transformI18n("system.notifyAccount"),
      illustrate: transformI18n("system.notifyAccountTip"),
      checked: true
    },
    {
      key: "notify_system",
      title: transformI18n("system.notifySystem"),
      illustrate: transformI18n("system.notifySystemTip"),
      checked: true
    },
    {
      key: "notify_task",
      title: transformI18n("system.notifyTask"),
      illustrate: transformI18n("system.notifyTaskTip"),
      checked: true
    }
  ]);

  async function loadPreferences() {
    const res = await getPreferences();
    if (res?.data) {
      for (const item of list.value) {
        if (res.data[item.key] !== undefined) {
          item.checked = res.data[item.key];
        }
      }
    }
  }

  async function onChange(val: boolean, item: (typeof list.value)[0]) {
    const oldValue = !val;
    const res = await updatePreferences({ [item.key]: val }).catch(() => null);
    if (res !== null) {
      message(`${item.title}${transformI18n("system.settingSuccess")}`, {
        type: "success"
      });
    } else {
      item.checked = oldValue;
      message(`${item.title}${transformI18n("system.settingFail")}`, {
        type: "error"
      });
    }
  }

  onMounted(() => {
    loadPreferences();
  });

  return { list, onChange };
}
