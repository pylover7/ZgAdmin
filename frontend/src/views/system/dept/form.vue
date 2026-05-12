<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { usePublicHooks } from "../hooks";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    id: "",
    higherDeptOptions: [],
    parentId: 0,
    name: "",
    principal: "",
    phone: "",
    email: "",
    sort: 0,
    status: 1,
    remark: ""
  })
});

const ruleFormRef = ref();
const { switchStyle } = usePublicHooks();
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
    <el-row :gutter="30">
      <re-col>
        <el-form-item :label="$t('system.parentDept')">
          <el-cascader
            v-model="newFormInline.parentId"
            class="w-full"
            :options="newFormInline.higherDeptOptions"
            :props="{
              value: 'id',
              label: 'name',
              emitPath: false,
              checkStrictly: true
            }"
            clearable
            filterable
            :placeholder="$t('system.pleaseSelect') + $t('system.parentDept')"
          >
            <template #default="{ node, data }">
              <span>{{ data.name }}</span>
              <span v-if="!node.isLeaf"> ({{ data.children.length }}) </span>
            </template>
          </el-cascader>
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.deptName')" prop="name">
          <el-input
            v-model="newFormInline.name"
            clearable
            :placeholder="$t('system.pleaseInput') + $t('system.deptName')"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.principal')">
          <el-input
            v-model="newFormInline.principal"
            clearable
            :placeholder="$t('system.pleaseInput') + $t('system.principal')"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.phone')" prop="phone">
          <el-input
            v-model="newFormInline.phone"
            clearable
            :placeholder="$t('system.pleaseInput') + $t('system.phone')"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.email')" prop="email">
          <el-input
            v-model="newFormInline.email"
            clearable
            :placeholder="$t('system.pleaseInput') + $t('system.email')"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.sort')">
          <el-input-number
            v-model="newFormInline.sort"
            class="w-full!"
            :min="0"
            :max="9999"
            controls-position="right"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.status')">
          <el-switch
            v-model="newFormInline.status"
            inline-prompt
            :active-value="1"
            :inactive-value="0"
            :active-text="$t('system.enabled')"
            :inactive-text="$t('system.disabled')"
            :style="switchStyle"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item :label="$t('system.remark')">
          <el-input
            v-model="newFormInline.remark"
            :placeholder="$t('system.pleaseInput') + $t('system.remark')"
            type="textarea"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
