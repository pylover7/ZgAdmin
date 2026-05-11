<script setup lang="ts">
import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { Connection, ChatDotRound } from "@element-plus/icons-vue";
import { transformI18n } from "@/plugins/i18n";
import {
  getLoginConfig,
  updateLoginConfig,
  type LoginConfig,
  type LoginConfigRules
} from "@/api/settings";

defineOptions({
  name: "LoginSettings"
});

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

// 保存初始配置用于比较
const initialForm = ref<LoginConfig | null>(null);

const rules: LoginConfigRules = {
  qq: {
    app_id: [
      {
        required: true,
        message: "请输入QQ App ID",
        trigger: "blur"
      }
    ],
    app_key: [
      {
        required: true,
        message: "请输入QQ App Key",
        trigger: "blur"
      }
    ],
    redirect_uri: [
      {
        required: true,
        message: "请输入QQ回调地址",
        trigger: "blur"
      },
      {
        pattern: /^https?:\/\/.+/,
        message: "请输入正确的URL地址",
        trigger: "blur"
      }
    ]
  },
  wechat: {
    app_id: [
      {
        required: true,
        message: "请输入微信 App ID",
        trigger: "blur"
      }
    ],
    app_secret: [
      {
        required: true,
        message: "请输入微信 App Secret",
        trigger: "blur"
      }
    ],
    redirect_uri: [
      {
        required: true,
        message: "请输入微信回调地址",
        trigger: "blur"
      },
      {
        pattern: /^https?:\/\/.+/,
        message: "请输入正确的URL地址",
        trigger: "blur"
      }
    ]
  }
};

// 将嵌套的规则转换为 Element Plus 需要的格式
const getRules = (path: string, field: string) => {
  const keys = path.split(".");
  const obj = keys.reduce((acc: any, key: string) => acc?.[key], rules);
  return obj?.[field] || [];
};

// 判断表单是否有修改
const hasChanges = computed(() => {
  if (!initialForm.value) return false;

  const current = JSON.stringify(loginForm);
  const initial = JSON.stringify(initialForm.value);
  return current !== initial;
});

// 判断是否可以保存（有启用的登录方式或表单有修改）
const canSave = computed(() => {
  const hasEnabled = loginForm.qq.enabled || loginForm.wechat.enabled;
  return hasEnabled || hasChanges.value;
});

/** 获取登录配置 */
const fetchLoginConfig = async () => {
  try {
    loading.value = true;
    const { data } = await getLoginConfig();
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
      // 保存初始配置
      initialForm.value = JSON.parse(JSON.stringify(loginForm));
    }
  } catch (error) {
    console.error("获取登录配置失败:", error);
  } finally {
    loading.value = false;
  }
};

/** 保存配置 */
const handleSave = async () => {
  if (!formRef.value) return;

  try {
    // 验证所有已启用的登录方式配置
    await formRef.value.validate();

    loading.value = true;
    await updateLoginConfig(loginForm);
    ElMessage.success(
      transformI18n("system.save") + transformI18n("system.success")
    );
    // 更新初始配置
    initialForm.value = JSON.parse(JSON.stringify(loginForm));
  } catch (error) {
    if (error !== false) {
      ElMessage.error(
        transformI18n("system.save") + transformI18n("system.fail")
      );
      console.error("保存登录配置失败:", error);
    }
  } finally {
    loading.value = false;
  }
};

/** 重置配置 */
const handleReset = async () => {
  try {
    await ElMessageBox.confirm("确定要重置所有登录配置吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
    await fetchLoginConfig();
    ElMessage.success("已重置");
  } catch {
    // 用户取消
  }
};

onMounted(() => {
  fetchLoginConfig();
});
</script>

<template>
  <div class="login-settings">
    <el-card v-loading="loading" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">登录配置</span>
          <div class="actions">
            <el-button @click="handleReset">重置</el-button>
            <el-button type="primary" :disabled="!canSave" @click="handleSave">
              保存
            </el-button>
          </div>
        </div>
      </template>

      <el-form ref="formRef" :model="loginForm" label-width="150px">
        <!-- QQ登录配置 -->
        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><Connection /></el-icon>
            <span>{{ $t("login.QQLogin") }}</span>
            <el-switch v-model="loginForm.qq.enabled" />
          </div>
        </el-divider>

        <el-alert
          v-if="!loginForm.qq.enabled"
          title="QQ登录已禁用"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <el-form-item
          :label="$t('system.appId')"
          prop="qq.app_id"
          :rules="loginForm.qq.enabled ? getRules('qq', 'app_id') : []"
        >
          <el-input
            v-model="loginForm.qq.app_id"
            :placeholder="$t('system.pleaseInput') + $t('system.appId')"
            :disabled="!loginForm.qq.enabled"
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.appKey')"
          prop="qq.app_key"
          :rules="loginForm.qq.enabled ? getRules('qq', 'app_key') : []"
        >
          <el-input
            v-model="loginForm.qq.app_key"
            type="password"
            :placeholder="$t('system.pleaseInput') + $t('system.appKey')"
            :disabled="!loginForm.qq.enabled"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.redirectUri')"
          prop="qq.redirect_uri"
          :rules="loginForm.qq.enabled ? getRules('qq', 'redirect_uri') : []"
        >
          <el-input
            v-model="loginForm.qq.redirect_uri"
            :placeholder="$t('system.pleaseInput') + $t('system.redirectUri')"
            :disabled="!loginForm.qq.enabled"
            clearable
          />
          <template #tip>
            <div class="tip-text">
              此地址需要在QQ互联后台的回调域名中配置，格式如：
              http://localhost:7000/login/qq/callback
            </div>
          </template>
        </el-form-item>

        <!-- 微信登录配置 -->
        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ $t("login.WeChatLogin") }}</span>
            <el-switch v-model="loginForm.wechat.enabled" />
          </div>
        </el-divider>

        <el-alert
          v-if="!loginForm.wechat.enabled"
          title="微信登录已禁用"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <el-form-item
          :label="$t('system.appId')"
          prop="wechat.app_id"
          :rules="loginForm.wechat.enabled ? getRules('wechat', 'app_id') : []"
        >
          <el-input
            v-model="loginForm.wechat.app_id"
            :placeholder="$t('system.pleaseInput') + $t('system.appId')"
            :disabled="!loginForm.wechat.enabled"
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.appKey')"
          prop="wechat.app_secret"
          :rules="
            loginForm.wechat.enabled ? getRules('wechat', 'app_secret') : []
          "
        >
          <el-input
            v-model="loginForm.wechat.app_secret"
            type="password"
            :placeholder="$t('system.pleaseInput') + $t('system.appKey')"
            :disabled="!loginForm.wechat.enabled"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.redirectUri')"
          prop="wechat.redirect_uri"
          :rules="
            loginForm.wechat.enabled ? getRules('wechat', 'redirect_uri') : []
          "
        >
          <el-input
            v-model="loginForm.wechat.redirect_uri"
            :placeholder="$t('system.pleaseInput') + $t('system.redirectUri')"
            :disabled="!loginForm.wechat.enabled"
            clearable
          />
          <template #tip>
            <div class="tip-text">
              此地址需要在微信开放平台后台的回调域名中配置，格式如：
              http://localhost:7000/login/wechat/callback
            </div>
          </template>
        </el-form-item>
      </el-form>

      <!-- 配置说明 -->
      <el-divider content-position="left">配置说明</el-divider>

      <div class="help-content">
        <h4>QQ登录配置步骤：</h4>
        <ol>
          <li>
            访问
            <el-link
              type="primary"
              href="https://connect.qq.com/"
              target="_blank"
              >QQ互联</el-link
            >
            并登录
          </li>
          <li>创建应用，获取 App ID 和 App Key</li>
          <li>配置回调域名，格式需与上方填写的一致</li>
          <li>等待审核通过后即可使用</li>
        </ol>

        <h4>微信登录配置步骤：</h4>
        <ol>
          <li>
            访问
            <el-link
              type="primary"
              href="https://open.weixin.qq.com/"
              target="_blank"
              >微信开放平台</el-link
            >
            并登录
          </li>
          <li>创建网站应用，获取 AppID 和 AppSecret</li>
          <li>配置授权回调域名，格式需与上方填写的一致</li>
          <li>等待审核通过后即可使用</li>
        </ol>
      </div>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.login-settings {
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

  .tip-text {
    margin-top: 4px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .help-content {
    padding: 20px;
    background: var(--el-fill-color-light);
    border-radius: 4px;

    h4 {
      margin: 16px 0 8px;
      font-weight: 500;
      color: var(--el-text-color-primary);

      &:first-child {
        margin-top: 0;
      }
    }

    ol {
      padding-left: 20px;
      color: var(--el-text-color-regular);

      li {
        margin: 6px 0;
        line-height: 1.6;
      }
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
