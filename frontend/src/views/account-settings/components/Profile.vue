<script setup lang="ts">
import { onMounted } from "vue";
import { deviceDetection } from "@pureadmin/utils";
import { useProfile } from "../utils/useProfile";
import { transformI18n } from "@/plugins/i18n";

defineOptions({
  name: "Profile"
});

const {
  loading,
  userInfoFormRef,
  userInfos,
  rules,
  queryEmail,
  onSubmit,
  loadProfile
} = useProfile();

onMounted(() => {
  loadProfile();
});
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">{{ transformI18n("system.profile") }}</h3>
    <el-form
      ref="userInfoFormRef"
      label-position="top"
      :rules="rules"
      :model="userInfos"
    >
      <el-form-item :label="transformI18n('system.nickname')" prop="nickname">
        <el-input
          v-model="userInfos.nickname"
          :placeholder="transformI18n('system.pleaseEnterNickname')"
        />
      </el-form-item>
      <el-form-item :label="transformI18n('system.email')" prop="email">
        <el-autocomplete
          v-model="userInfos.email"
          :fetch-suggestions="queryEmail"
          :trigger-on-focus="false"
          :placeholder="transformI18n('system.pleaseEnterEmail')"
          clearable
          class="w-full"
        />
      </el-form-item>
      <el-form-item :label="transformI18n('system.contactPhone')">
        <el-input
          v-model="userInfos.phone"
          :placeholder="transformI18n('system.pleaseEnterContactPhone')"
          clearable
        />
      </el-form-item>
      <el-form-item :label="transformI18n('system.introduction')">
        <el-input
          v-model="userInfos.remark"
          :placeholder="transformI18n('system.pleaseEnterIntroduction')"
          type="textarea"
          :autosize="{ minRows: 6, maxRows: 8 }"
          maxlength="56"
          show-word-limit
        />
      </el-form-item>
      <el-button
        type="primary"
        :loading="loading"
        @click="onSubmit(userInfoFormRef)"
      >
        {{ transformI18n("system.updateProfile") }}
      </el-button>
    </el-form>
  </div>
</template>
