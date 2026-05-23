<script setup lang="ts">
import { ref } from "vue";
import { Lock, Key, Warning } from "@element-plus/icons-vue";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { useSecuritySettings } from "./utils/hook";
import Delete from "~icons/ep/delete";

defineOptions({
  name: "SecuritySettings"
});

const {
  policyRef,
  policyLoading,
  policyForm,
  policyChanged,
  savePolicy,
  ipLoading,
  ipRules,
  ipColumns,
  openAddDialog,
  openEditDialog,
  handleDeleteIPRules
} = useSecuritySettings();

const tableRef = ref();
</script>

<template>
  <div class="main">
    <!-- 安全策略配置 -->
    <el-card v-loading="policyLoading" shadow="never" class="mb-5 border-0!">
      <template #header>
        <div class="flex-bc">
          <span
            class="flex gap-2 items-center text-lg font-semibold text-(--el-text-color-primary)"
          >
            <el-icon><Lock /></el-icon>
            {{ $t("system.security.policyConfig") }}
          </span>
          <el-button
            type="primary"
            :disabled="!policyChanged"
            @click="savePolicy"
          >
            {{ $t("system.security.savePolicy") }}
          </el-button>
        </div>
      </template>

      <el-form
        ref="policyRef"
        :model="policyForm"
        label-width="160px"
        label-position="right"
      >
        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><Key /></el-icon>
            {{ $t("system.security.passwordPolicy") }}
          </div>
        </el-divider>

        <el-form-item :label="$t('system.security.minPasswordLength')">
          <el-input-number
            v-model="policyForm.min_password_length"
            :min="6"
            :max="32"
          />
        </el-form-item>

        <el-form-item :label="$t('system.security.requireUppercase')">
          <el-switch v-model="policyForm.require_uppercase" />
        </el-form-item>

        <el-form-item :label="$t('system.security.requireLowercase')">
          <el-switch v-model="policyForm.require_lowercase" />
        </el-form-item>

        <el-form-item :label="$t('system.security.requireDigit')">
          <el-switch v-model="policyForm.require_digit" />
        </el-form-item>

        <el-form-item :label="$t('system.security.requireSpecial')">
          <el-switch v-model="policyForm.require_special" />
        </el-form-item>

        <el-form-item :label="$t('system.security.passwordHistory')">
          <el-input-number
            v-model="policyForm.password_history_count"
            :min="0"
            :max="24"
          />
          <span class="ml-3 text-xs text-(--el-text-color-secondary)">
            {{ $t("system.security.passwordHistoryTip") }}
          </span>
        </el-form-item>

        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><Lock /></el-icon>
            {{ $t("system.security.loginProtection") }}
          </div>
        </el-divider>

        <el-form-item :label="$t('system.security.maxLoginAttempts')">
          <el-input-number
            v-model="policyForm.max_login_attempts"
            :min="3"
            :max="20"
          />
          <span class="ml-3 text-xs text-(--el-text-color-secondary)">
            {{ $t("system.security.maxLoginAttemptsTip") }}
          </span>
        </el-form-item>

        <el-form-item :label="$t('system.security.lockoutDuration')">
          <el-input-number
            v-model="policyForm.lockout_duration_minutes"
            :min="5"
            :max="1440"
          />
          <span class="ml-3 text-xs text-(--el-text-color-secondary)">
            {{ $t("system.security.lockoutDurationTip") }}
          </span>
        </el-form-item>

        <el-form-item :label="$t('system.security.captchaEnabled')">
          <el-switch v-model="policyForm.captcha_enabled" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- IP 黑白名单 -->
    <el-card v-loading="ipLoading" shadow="never" class="border-0!">
      <template #header>
        <div class="flex-bc">
          <span
            class="flex gap-2 items-center text-lg font-semibold text-(--el-text-color-primary)"
          >
            <el-icon><Warning /></el-icon>
            {{ $t("system.security.ipBlackWhiteList") }}
          </span>
          <el-button type="primary" @click="openAddDialog">
            {{ $t("system.security.addRule") }}
          </el-button>
        </div>
      </template>

      <el-alert
        :title="$t('system.security.ipPriorityNote')"
        type="info"
        :closable="false"
        show-icon
        class="mb-4"
      />

      <pure-table
        ref="tableRef"
        row-key="id"
        :data="ipRules"
        :columns="ipColumns"
        :header-cell-style="{
          background: 'var(--el-fill-color-light)',
          color: 'var(--el-text-color-primary)'
        }"
      >
        <template #operation="{ row, size }">
          <el-button
            class="reset-margin"
            link
            type="primary"
            :size="size"
            @click="openEditDialog(row)"
          >
            {{ $t("system.edit") }}
          </el-button>
          <el-popconfirm
            :title="$t('system.deleteConfirm')"
            @confirm="handleDeleteIPRules([row.id])"
          >
            <template #reference>
              <el-button
                class="reset-margin"
                link
                type="danger"
                :size="size"
                :icon="useRenderIcon(Delete)"
              >
                {{ $t("system.delete") }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </pure-table>

      <el-empty
        v-if="ipRules.length === 0"
        :description="$t('system.security.noIpRules')"
      />
    </el-card>
  </div>
</template>

<style lang="scss" scoped></style>
