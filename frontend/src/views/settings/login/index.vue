<script setup lang="ts">
import { Connection, ChatDotRound } from "@element-plus/icons-vue";
import { useLoginSettings } from "./utils/hook";

defineOptions({
  name: "LoginSettings"
});

const {
  formRef,
  loading,
  loginForm,
  hasChanges,
  canSave,
  getRules,
  handleSave,
  handleReset
} = useLoginSettings();
</script>

<template>
  <div class="main">
    <el-card v-loading="loading" shadow="never" class="border-0!">
      <template #header>
        <div class="flex-bc">
          <span class="text-lg font-semibold text-(--el-text-color-primary)">
            {{ $t("system.loginSettings.title") }}
          </span>
          <div class="flex gap-3">
            <el-button @click="handleReset">{{ $t("system.reset") }}</el-button>
            <el-button type="primary" :disabled="!canSave" @click="handleSave">
              {{ $t("system.save") }}
            </el-button>
          </div>
        </div>
      </template>

      <el-form ref="formRef" :model="loginForm" label-width="150px">
        <!-- QQ登录配置 -->
        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><Connection /></el-icon>
            <span>{{ $t("login.QQLogin") }}</span>
            <el-switch v-model="loginForm.qq.enabled" />
          </div>
        </el-divider>

        <el-alert
          v-if="!loginForm.qq.enabled"
          :title="$t('system.qqLoginDisabled')"
          type="info"
          :closable="false"
          class="mb-5"
        />

        <el-form-item
          :label="$t('system.settings.appId')"
          prop="qq.app_id"
          :rules="getRules('qq', 'app_id', loginForm.qq.enabled)"
        >
          <el-input
            v-model="loginForm.qq.app_id"
            :placeholder="
              $t('system.pleaseInput') + $t('system.settings.appId')
            "
            :disabled="!loginForm.qq.enabled"
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.settings.appKey')"
          prop="qq.app_key"
          :rules="getRules('qq', 'app_key', loginForm.qq.enabled)"
        >
          <el-input
            v-model="loginForm.qq.app_key"
            type="password"
            :placeholder="
              $t('system.pleaseInput') + $t('system.settings.appKey')
            "
            :disabled="!loginForm.qq.enabled"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.settings.redirectUri')"
          prop="qq.redirect_uri"
          :rules="getRules('qq', 'redirect_uri', loginForm.qq.enabled)"
        >
          <el-input
            v-model="loginForm.qq.redirect_uri"
            :placeholder="
              $t('system.pleaseInput') + $t('system.settings.redirectUri')
            "
            :disabled="!loginForm.qq.enabled"
            clearable
          />
          <template #tip>
            <div class="mt-1 text-xs text-(--el-text-color-secondary)">
              {{ $t("system.qqRedirectTip") }}
            </div>
          </template>
        </el-form-item>

        <!-- 微信登录配置 -->
        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ $t("login.WeChatLogin") }}</span>
            <el-switch v-model="loginForm.wechat.enabled" />
          </div>
        </el-divider>

        <el-alert
          v-if="!loginForm.wechat.enabled"
          :title="$t('system.wechatLoginDisabled')"
          type="info"
          :closable="false"
          class="mb-5"
        />

        <el-form-item
          :label="$t('system.settings.appId')"
          prop="wechat.app_id"
          :rules="getRules('wechat', 'app_id', loginForm.wechat.enabled)"
        >
          <el-input
            v-model="loginForm.wechat.app_id"
            :placeholder="
              $t('system.pleaseInput') + $t('system.settings.appId')
            "
            :disabled="!loginForm.wechat.enabled"
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.settings.appKey')"
          prop="wechat.app_secret"
          :rules="getRules('wechat', 'app_secret', loginForm.wechat.enabled)"
        >
          <el-input
            v-model="loginForm.wechat.app_secret"
            type="password"
            :placeholder="
              $t('system.pleaseInput') + $t('system.settings.appKey')
            "
            :disabled="!loginForm.wechat.enabled"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item
          :label="$t('system.settings.redirectUri')"
          prop="wechat.redirect_uri"
          :rules="getRules('wechat', 'redirect_uri', loginForm.wechat.enabled)"
        >
          <el-input
            v-model="loginForm.wechat.redirect_uri"
            :placeholder="
              $t('system.pleaseInput') + $t('system.settings.redirectUri')
            "
            :disabled="!loginForm.wechat.enabled"
            clearable
          />
          <template #tip>
            <div class="mt-1 text-xs text-(--el-text-color-secondary)">
              {{ $t("system.wechatRedirectTip") }}
            </div>
          </template>
        </el-form-item>
      </el-form>

      <!-- 配置说明 -->
      <el-divider content-position="left">
        {{ $t("system.configGuide") }}
      </el-divider>

      <div class="p-5 bg-(--el-fill-color-light) rounded">
        <h4 class="mt-0 mb-2 font-medium text-(--el-text-color-primary)">
          {{ $t("system.qqConfigSteps") }}
        </h4>
        <ol class="pl-5 text-(--el-text-color-regular)">
          <li class="my-1.5 leading-relaxed">
            {{ $t("system.qqStep1") }}
            <el-link
              type="primary"
              href="https://connect.qq.com/"
              target="_blank"
            >
              {{ $t("system.qqConnect") }}
            </el-link>
          </li>
          <li class="my-1.5 leading-relaxed">{{ $t("system.qqStep2") }}</li>
          <li class="my-1.5 leading-relaxed">{{ $t("system.qqStep3") }}</li>
          <li class="my-1.5 leading-relaxed">{{ $t("system.qqStep4") }}</li>
        </ol>

        <h4 class="mt-4 mb-2 font-medium text-(--el-text-color-primary)">
          {{ $t("system.wechatConfigSteps") }}
        </h4>
        <ol class="pl-5 text-(--el-text-color-regular)">
          <li class="my-1.5 leading-relaxed">
            {{ $t("system.wechatStep1") }}
            <el-link
              type="primary"
              href="https://open.weixin.qq.com/"
              target="_blank"
            >
              {{ $t("system.wechatOpenPlatform") }}
            </el-link>
          </li>
          <li class="my-1.5 leading-relaxed">{{ $t("system.wechatStep2") }}</li>
          <li class="my-1.5 leading-relaxed">{{ $t("system.wechatStep3") }}</li>
          <li class="my-1.5 leading-relaxed">{{ $t("system.wechatStep4") }}</li>
        </ol>
      </div>
    </el-card>
  </div>
</template>

<style lang="scss" scoped></style>
