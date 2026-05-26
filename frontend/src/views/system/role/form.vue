<script setup lang="ts">
import { ref } from "vue";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    name: "",
    code: "",
    remark: ""
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
    <el-form-item :label="$t('system.roleName')" prop="name">
      <el-input
        v-model="newFormInline.name"
        clearable
        :placeholder="$t('system.enterRoleName')"
      />
    </el-form-item>

    <el-form-item :label="$t('system.roleCode')" prop="code">
      <el-input
        v-model="newFormInline.code"
        clearable
        :placeholder="$t('system.enterRoleCode')"
      />
    </el-form-item>

    <el-form-item :label="$t('system.remark')">
      <el-input
        v-model="newFormInline.remark"
        :placeholder="$t('system.remarkPlaceholder')"
        type="textarea"
      />
    </el-form-item>
  </el-form>
</template>
