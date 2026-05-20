<script setup lang="ts">
import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { Setting, Tools, Document } from "@element-plus/icons-vue";
import { transformI18n } from "@/plugins/i18n";
import { getConfig, setConfig } from "@/config";
import {
  getGeneralConfig,
  updateGeneralConfig,
  type GeneralConfig,
  type GeneralConfigRules
} from "@/api/settings";

defineOptions({
  name: "GenSettings"
});

const formRef = ref<FormInstance>();
const loading = ref(false);

const generalForm = reactive<GeneralConfig>({
  site_name: "ZgAdmin",
  site_desc: "一个开源的在线工具箱",
  logo: "",
  default_lang: "zh-CN",
  enable_email: false,
  copyright: "",
  icp: ""
});

// 保存初始配置用于比较
const initialForm = ref<GeneralConfig | null>(null);

// 语言选项
const langOptions = [
  { label: "简体中文", value: "zh-CN" },
  { label: "English", value: "en" }
];

const rules: GeneralConfigRules = {
  site_name: [
    { required: true, message: "请输入站点名称", trigger: "blur" },
    { max: 50, message: "站点名称不超过50个字符", trigger: "blur" }
  ],
  site_desc: [
    { max: 200, message: "站点描述不超过200个字符", trigger: "blur" }
  ],
  default_lang: [
    { required: true, message: "请选择默认语言", trigger: "change" }
  ]
};

// 判断表单是否有修改
const hasChanges = computed(() => {
  if (!initialForm.value) return false;
  return JSON.stringify(generalForm) !== JSON.stringify(initialForm.value);
});

/** 获取通用配置 */
const fetchGeneralConfig = async () => {
  try {
    loading.value = true;
    const { data } = await getGeneralConfig();
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
  } catch (error) {
    console.error("获取通用配置失败:", error);
  } finally {
    loading.value = false;
  }
};

/** 保存配置 */
const handleSave = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
    loading.value = true;
    await updateGeneralConfig(generalForm);
    ElMessage.success(
      transformI18n("system.save") + transformI18n("system.success")
    );
    initialForm.value = JSON.parse(JSON.stringify(generalForm));

    // 同步更新全局配置，使标题、语言等实时生效
    const currentConfig = getConfig();
    currentConfig.Title = generalForm.site_name;
    currentConfig.Locale = generalForm.default_lang;
    currentConfig.SiteDesc = generalForm.site_desc;
    currentConfig.Logo = generalForm.logo;
    currentConfig.Copyright = generalForm.copyright;
    currentConfig.Icp = generalForm.icp;
    setConfig(currentConfig);

    // 更新浏览器标签页标题
    document.title = generalForm.site_name;
  } catch (error) {
    if (error !== false) {
      ElMessage.error(
        transformI18n("system.save") + transformI18n("system.fail")
      );
      console.error("保存通用配置失败:", error);
    }
  } finally {
    loading.value = false;
  }
};

/** 重置配置 */
const handleReset = async () => {
  try {
    await ElMessageBox.confirm("确定要重置所有通用配置吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
    await fetchGeneralConfig();
    ElMessage.success("已重置");
  } catch {
    // 用户取消
  }
};

onMounted(() => {
  fetchGeneralConfig();
});
</script>

<template>
  <div class="general-settings">
    <el-card v-loading="loading" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">{{ $t("system.generalSettings.title") }}</span>
          <div class="actions">
            <el-button @click="handleReset">{{ $t("system.reset") }}</el-button>
            <el-button
              type="primary"
              :disabled="!hasChanges"
              @click="handleSave"
            >
              {{ $t("system.save") }}
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="generalForm"
        :rules="rules"
        label-width="150px"
      >
        <!-- 站点基本信息 -->
        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><Setting /></el-icon>
            <span>站点信息</span>
          </div>
        </el-divider>

        <el-form-item
          :label="$t('system.generalSettings.siteName')"
          prop="site_name"
        >
          <el-input
            v-model="generalForm.site_name"
            :placeholder="
              $t('system.pleaseInput') + $t('system.generalSettings.siteName')
            "
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.generalSettings.siteDesc')"
          prop="site_desc"
        >
          <el-input
            v-model="generalForm.site_desc"
            type="textarea"
            :rows="3"
            :placeholder="
              $t('system.pleaseInput') + $t('system.generalSettings.siteDesc')
            "
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item :label="$t('system.generalSettings.logo')" prop="logo">
          <el-input
            v-model="generalForm.logo"
            :placeholder="$t('system.pleaseInput') + 'Logo URL'"
            clearable
          />
          <div v-if="generalForm.logo" class="logo-preview">
            <el-image
              :src="generalForm.logo"
              fit="contain"
              style="width: 60px; height: 60px"
            >
              <template #error>
                <div class="image-error">加载失败</div>
              </template>
            </el-image>
          </div>
        </el-form-item>

        <!-- 功能设置 -->
        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><Tools /></el-icon>
            <span>功能设置</span>
          </div>
        </el-divider>

        <el-form-item
          :label="$t('system.generalSettings.defaultLang')"
          prop="default_lang"
        >
          <el-select v-model="generalForm.default_lang" style="width: 240px">
            <el-option
              v-for="item in langOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('system.generalSettings.enableEmail')">
          <el-switch v-model="generalForm.enable_email" />
          <span class="form-tip">关闭后系统将不发送任何邮件通知</span>
        </el-form-item>

        <!-- 其他信息 -->
        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><Document /></el-icon>
            <span>其他信息</span>
          </div>
        </el-divider>

        <el-form-item :label="$t('system.generalSettings.copyright')">
          <el-input
            v-model="generalForm.copyright"
            placeholder="如：Copyright © 2024 ZgAdmin"
            clearable
          />
        </el-form-item>

        <el-form-item :label="$t('system.generalSettings.icp')">
          <el-input
            v-model="generalForm.icp"
            placeholder="如：京ICP备XXXXXXXX号"
            clearable
          />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.general-settings {
  padding: 20px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .title {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .actions {
      display: flex;
      gap: 12px;
    }
  }

  .divider-title {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 16px;
    font-weight: 500;
  }

  .form-tip {
    margin-left: 12px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .logo-preview {
    display: inline-block;
    padding: 8px;
    margin-top: 8px;
    background: var(--el-fill-color-light);
    border-radius: 4px;

    .image-error {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 60px;
      height: 60px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  :deep(.el-card__body) {
    padding: 20px;
  }

  :deep(.el-divider) {
    margin: 24px 0;
  }
}
</style>
