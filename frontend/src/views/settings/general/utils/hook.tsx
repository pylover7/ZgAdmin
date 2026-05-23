import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance } from "element-plus";
import { transformI18n } from "@/plugins/i18n";
import { getConfig, setConfig } from "@/config";
import { getGeneralConfig, updateGeneralConfig } from "@/api/settings";
import type { GeneralConfig } from "@/types/settings";

/** 语言选项 */
const langOptions = [
  { label: "简体中文", value: "zh-CN" },
  { label: "English", value: "en" }
];

/** 表单校验规则 */
const formRules = {
  site_name: [
    {
      required: true,
      message:
        transformI18n("system.pleaseInput") +
        transformI18n("system.generalSettings.siteName"),
      trigger: "blur"
    },
    {
      max: 50,
      message: transformI18n("system.siteNameMax"),
      trigger: "blur"
    }
  ],
  site_desc: [
    {
      max: 200,
      message: transformI18n("system.siteDescMax"),
      trigger: "blur"
    }
  ],
  default_lang: [
    {
      required: true,
      message: transformI18n("system.pleaseSelectLang"),
      trigger: "change"
    }
  ]
};

export function useGeneralSettings() {
  const formRef = ref<FormInstance>();
  const loading = ref(false);

  const generalForm = reactive<GeneralConfig>({
    site_name: "ZgAdmin",
    site_desc: "",
    logo: "",
    default_lang: "zh-CN",
    enable_email: false,
    copyright: "",
    icp: ""
  });

  const initialForm = ref<GeneralConfig | null>(null);

  const hasChanges = computed(() => {
    if (!initialForm.value) return false;
    return JSON.stringify(generalForm) !== JSON.stringify(initialForm.value);
  });

  /** 获取通用配置 */
  const fetchGeneralConfig = async () => {
    loading.value = true;
    const { data } = await getGeneralConfig().catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return { data: null };
    });
    if (data) {
      Object.assign(generalForm, {
        site_name: data.site_name || "ZgAdmin",
        site_desc: data.site_desc || "",
        logo: data.logo || "",
        default_lang: data.default_lang || "zh-CN",
        enable_email: data.enable_email === true,
        copyright: data.copyright || "",
        icp: data.icp || ""
      });
      initialForm.value = JSON.parse(JSON.stringify(generalForm));
    }
    loading.value = false;
  };

  /** 保存配置 */
  const handleSave = async () => {
    const valid = await formRef.value?.validate().catch(() => null);
    if (!valid) return;

    loading.value = true;
    const res = await updateGeneralConfig(generalForm).catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return null;
    });
    loading.value = false;

    if (res) {
      ElMessage.success(transformI18n("system.saveSuccess"));
      initialForm.value = JSON.parse(JSON.stringify(generalForm));

      // 同步更新全局配置
      const currentConfig = getConfig();
      currentConfig.Title = generalForm.site_name;
      currentConfig.Locale = generalForm.default_lang;
      currentConfig.SiteDesc = generalForm.site_desc;
      currentConfig.Logo = generalForm.logo;
      currentConfig.Copyright = generalForm.copyright;
      currentConfig.Icp = generalForm.icp;
      setConfig(currentConfig);
      document.title = generalForm.site_name;
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
    // 用户确认后重新获取配置
    await fetchGeneralConfig();
    ElMessage.success(transformI18n("system.resetSuccess"));
  };

  onMounted(() => {
    fetchGeneralConfig();
  });

  return {
    formRef,
    loading,
    generalForm,
    formRules,
    langOptions,
    hasChanges,
    handleSave,
    handleReset
  };
}
