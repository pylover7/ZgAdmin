<script setup lang="ts">
import { ref } from "vue";
import { formRules } from "./utils/rule";
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
    <el-form-item label="通知标题" prop="title">
      <el-input
        v-model="newFormInline.title"
        clearable
        placeholder="请输入通知标题"
        maxlength="200"
        show-word-limit
      />
    </el-form-item>

    <el-form-item label="通知类型" prop="type">
      <el-select
        v-model="newFormInline.type"
        placeholder="请选择通知类型"
        class="w-full"
      >
        <el-option label="系统通知" :value="0" />
        <el-option label="业务通知" :value="1" />
        <el-option label="公告" :value="2" />
      </el-select>
    </el-form-item>

    <el-form-item label="通知级别" prop="level">
      <el-select
        v-model="newFormInline.level"
        placeholder="请选择通知级别"
        class="w-full"
      >
        <el-option label="普通" value="info" />
        <el-option label="警告" value="warning" />
        <el-option label="重要" value="important" />
      </el-select>
    </el-form-item>

    <el-form-item label="通知内容">
      <el-input
        v-model="newFormInline.content"
        placeholder="请输入通知内容"
        type="textarea"
        :rows="4"
      />
    </el-form-item>

    <el-form-item label="通知状态">
      <el-radio-group v-model="newFormInline.status">
        <el-radio :value="0">草稿</el-radio>
        <el-radio :value="1">已发布</el-radio>
      </el-radio-group>
    </el-form-item>
  </el-form>
</template>
