<script setup lang="ts">
import { Setting, Tools, Document } from "@element-plus/icons-vue";
import { useGeneralSettings } from "./utils/hook";

defineOptions({
  name: "GenSettings"
});

const {
  formRef,
  loading,
  generalForm,
  formRules,
  langOptions,
  hasChanges,
  handleSave,
  handleReset
} = useGeneralSettings();
</script>

<template>
  <div class="main">
    <el-card v-loading="loading" shadow="never" class="border-0!">
      <template #header>
        <div class="flex-bc">
          <span class="text-lg font-semibold text-(--el-text-color-primary)">
            {{ $t("system.generalSettings.title") }}
          </span>
          <div class="flex gap-3">
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
        :rules="formRules"
        label-width="150px"
      >
        <!-- 站点基本信息 -->
        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><Setting /></el-icon>
            <span>{{ $t("system.siteInfo") }}</span>
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
          <div
            v-if="generalForm.logo"
            class="inline-block p-2 mt-2 bg-(--el-fill-color-light) rounded"
          >
            <el-image :src="generalForm.logo" fit="contain" class="size-15">
              <template #error>
                <div
                  class="flex-c size-15 text-xs text-(--el-text-color-secondary)"
                >
                  {{ $t("system.loadFailed") }}
                </div>
              </template>
            </el-image>
          </div>
        </el-form-item>

        <!-- 功能设置 -->
        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><Tools /></el-icon>
            <span>{{ $t("system.funcSettings") }}</span>
          </div>
        </el-divider>

        <el-form-item
          :label="$t('system.generalSettings.defaultLang')"
          prop="default_lang"
        >
          <el-select v-model="generalForm.default_lang" class="w-60">
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
          <span class="ml-3 text-xs text-(--el-text-color-secondary)">
            {{ $t("system.enableEmailTip") }}
          </span>
        </el-form-item>

        <!-- 其他信息 -->
        <el-divider content-position="left">
          <div class="flex gap-2 items-center text-base font-medium">
            <el-icon><Document /></el-icon>
            <span>{{ $t("system.otherInfo") }}</span>
          </div>
        </el-divider>

        <el-form-item :label="$t('system.generalSettings.copyright')">
          <el-input
            v-model="generalForm.copyright"
            :placeholder="$t('system.copyrightPlaceholder')"
            clearable
          />
        </el-form-item>

        <el-form-item :label="$t('system.generalSettings.icp')">
          <el-input
            v-model="generalForm.icp"
            :placeholder="$t('system.icpPlaceholder')"
            clearable
          />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style lang="scss" scoped></style>
