import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { transformI18n } from "@/plugins/i18n";
import { getLoginConfig, updateLoginConfig } from "@/api/settings";
import type { LoginConfig } from "@/types/settings";

/** QQ 校验规则 */
const qqRules: FormRules = {
  app_id: [
    {
      required: true,
      message: transformI18n("system.pleaseInput") + "QQ App ID",
      trigger: "blur"
    }
  ],
  app_key: [
    {
      required: true,
      message: transformI18n("system.pleaseInput") + "QQ App Key",
      trigger: "blur"
    }
  ],
  redirect_uri: [
    {
      required: true,
      message:
        transformI18n("system.pleaseInput") +
        transformI18n("system.redirectUri"),
      trigger: "blur"
    },
    {
      pattern: /^https?:\/\/.+/,
      message: transformI18n("system.invalidUrl"),
      trigger: "blur"
    }
  ]
};

/** 微信校验规则 */
const wechatRules: FormRules = {
  app_id: [
    {
      required: true,
      message: transformI18n("system.pleaseInput") + "WeChat App ID",
      trigger: "blur"
    }
  ],
  app_secret: [
    {
      required: true,
      message: transformI18n("system.pleaseInput") + "WeChat App Secret",
      trigger: "blur"
    }
  ],
  redirect_uri: [
    {
      required: true,
      message:
        transformI18n("system.pleaseInput") +
        transformI18n("system.redirectUri"),
      trigger: "blur"
    },
    {
      pattern: /^https?:\/\/.+/,
      message: transformI18n("system.invalidUrl"),
      trigger: "blur"
    }
  ]
};

/** 获取指定路径的规则 */
const getRules = (path: string, field: string, enabled: boolean) => {
  if (!enabled) return [];
  const rulesMap: Record<string, FormRules> = {
    qq: qqRules,
    wechat: wechatRules
  };
  const obj = rulesMap[path];
  return obj?.[field] ? [obj[field]].flat() : [];
};

export function useLoginSettings() {
  const formRef = ref<FormInstance>();
  const loading = ref(false);

  const loginForm = reactive<LoginConfig>({
    qq: {
      app_id: "",
      app_key: "",
      redirect_uri: "",
      enabled: false
    },
    wechat: {
      app_id: "",
      app_secret: "",
      redirect_uri: "",
      enabled: false
    }
  });

  const initialForm = ref<LoginConfig | null>(null);

  const hasChanges = computed(() => {
    if (!initialForm.value) return false;
    return JSON.stringify(loginForm) !== JSON.stringify(initialForm.value);
  });

  const canSave = computed(() => {
    const hasEnabled = loginForm.qq?.enabled || loginForm.wechat?.enabled;
    return hasEnabled || hasChanges.value;
  });

  /** 获取登录配置 */
  const fetchLoginConfig = async () => {
    loading.value = true;
    const { data } = await getLoginConfig().catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return { data: null };
    });
    if (data) {
      if (data.qq) {
        loginForm.qq = {
          app_id: data.qq.app_id || "",
          app_key: data.qq.app_key || "",
          redirect_uri: data.qq.redirect_uri || "",
          enabled: data.qq.enabled || false
        };
      }
      if (data.wechat) {
        loginForm.wechat = {
          app_id: data.wechat.app_id || "",
          app_secret: data.wechat.app_secret || "",
          redirect_uri: data.wechat.redirect_uri || "",
          enabled: data.wechat.enabled || false
        };
      }
      initialForm.value = JSON.parse(JSON.stringify(loginForm));
    }
    loading.value = false;
  };

  /** 保存配置 */
  const handleSave = async () => {
    const valid = await formRef.value?.validate().catch(() => null);
    if (!valid) return;

    loading.value = true;
    const res = await updateLoginConfig(loginForm).catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return null;
    });
    loading.value = false;

    if (res) {
      ElMessage.success(transformI18n("system.saveSuccess"));
      initialForm.value = JSON.parse(JSON.stringify(loginForm));
    }
  };

  /** 重置配置 */
  const handleReset = async () => {
    await ElMessageBox.confirm(
      transformI18n("system.resetConfirm"),
      transformI18n("system.tip"),
      {
        confirmButtonText: transformI18n("system.confirm"),
        cancelButtonText: transformI18n("system.cancel"),
        type: "warning"
      }
    ).catch(() => null);
    await fetchLoginConfig();
    ElMessage.success(transformI18n("system.resetSuccess"));
  };

  onMounted(() => {
    fetchLoginConfig();
  });

  return {
    formRef,
    loading,
    loginForm,
    hasChanges,
    canSave,
    getRules,
    handleSave,
    handleReset
  };
}
