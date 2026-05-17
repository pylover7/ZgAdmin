<script setup lang="ts">
import { ref } from "vue";
import { useFormRules } from "./utils/rule";
import { FormProps } from "./utils/types";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    id: "",
    title: "",
    content: "",
    type: 0,
    level: "info",
    status: 0
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);
const formRules = useFormRules();

function getRef() {
  return ruleFormRef.value;
}

defineExpose({ getRef });
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="newFormInline"
    :rules="formRules"
    label-width="82px"
  >
    <el-form-item :label="$t('system.notice.title')" prop="title">
      <el-input
        v-model="newFormInline.title"
        clearable
        :placeholder="$t('system.notice.enterTitle')"
        maxlength="200"
        show-word-limit
      />
    </el-form-item>

    <el-form-item :label="$t('system.notice.type')" prop="type">
      <el-select
        v-model="newFormInline.type"
        :placeholder="$t('system.notice.selectType')"
        class="w-full"
      >
        <el-option :label="$t('system.notice.sysNotice')" :value="0" />
        <el-option :label="$t('system.notice.bizNotice')" :value="1" />
        <el-option :label="$t('system.notice.announce')" :value="2" />
      </el-select>
    </el-form-item>

    <el-form-item :label="$t('system.notice.level')" prop="level">
      <el-select
        v-model="newFormInline.level"
        :placeholder="$t('system.notice.selectLevel')"
        class="w-full"
      >
        <el-option :label="$t('system.notice.info')" value="info" />
        <el-option :label="$t('system.notice.warn')" value="warning" />
        <el-option :label="$t('system.notice.important')" value="important" />
      </el-select>
    </el-form-item>

    <el-form-item :label="$t('system.notice.content')">
      <el-input
        v-model="newFormInline.content"
        :placeholder="$t('system.notice.enterContent')"
        type="textarea"
        :rows="4"
      />
    </el-form-item>

    <el-form-item :label="$t('system.notice.status')">
      <el-radio-group v-model="newFormInline.status">
        <el-radio :value="0">{{ $t("system.notice.draft") }}</el-radio>
        <el-radio :value="1">{{ $t("system.notice.published") }}</el-radio>
      </el-radio-group>
    </el-form-item>
  </el-form>
</template>
