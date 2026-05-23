<script setup lang="ts">
import { reactive } from "vue";
import { transformI18n } from "@/plugins/i18n";

defineOptions({
  name: "IpRuleForm"
});

const props = defineProps<{
  formInline: {
    id?: string;
    ip_cidr: string;
    rule_type: "whitelist" | "blacklist";
    description: string;
    is_active: boolean;
  };
}>();

const formData = reactive({ ...props.formInline });

/** 暴露给 ReDialog 的 beforeSure 获取数据 */
function getFormData() {
  return { ...formData };
}

defineExpose({ getFormData });
</script>

<template>
  <el-form :model="formData" label-width="100px">
    <el-form-item :label="$t('system.security.ipCidr')" required>
      <el-input
        v-model="formData.ip_cidr"
        :placeholder="$t('system.security.ipCidrPlaceholder')"
      />
    </el-form-item>
    <el-form-item :label="$t('system.security.ruleType')" required>
      <el-radio-group v-model="formData.rule_type">
        <el-radio value="blacklist">{{
          $t("system.security.blacklist")
        }}</el-radio>
        <el-radio value="whitelist">{{
          $t("system.security.whitelist")
        }}</el-radio>
      </el-radio-group>
    </el-form-item>
    <el-form-item :label="$t('system.security.description')">
      <el-input
        v-model="formData.description"
        type="textarea"
        :rows="2"
        :placeholder="$t('system.security.optionalRemark')"
      />
    </el-form-item>
    <el-form-item :label="$t('system.security.status')">
      <el-switch v-model="formData.is_active" />
    </el-form-item>
  </el-form>
</template>
