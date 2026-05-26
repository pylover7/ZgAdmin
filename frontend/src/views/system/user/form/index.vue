<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "../utils/rule";
import { FormProps } from "../utils/types";
import { usePublicHooks } from "../../hooks";
import { transformI18n } from "@/plugins/i18n";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    title: transformI18n("system.add"),
    higherDeptOptions: [],
    parentId: 0,
    nickname: "",
    username: "",
    password: "",
    phone: null,
    email: "",
    sex: 1,
    status: 1,
    remark: ""
  })
});

const sexOptions = [
  {
    value: 1,
    label: transformI18n("system.male")
  },
  {
    value: 0,
    label: transformI18n("system.female")
  }
];
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
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.userNickname')" prop="nickname">
          <el-input
            v-model="newFormInline.nickname"
            clearable
            :placeholder="$t('system.nicknamePlaceholder')"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.userName')" prop="username">
          <el-input
            v-model="newFormInline.username"
            clearable
            :placeholder="$t('system.usernamePlaceholder')"
          />
        </el-form-item>
      </re-col>

      <re-col
        v-if="newFormInline.title === transformI18n('system.add')"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.userPassword')" prop="password">
          <el-input
            v-model="newFormInline.password"
            clearable
            :placeholder="$t('system.passwordPlaceholder')"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.userPhone')" prop="phone">
          <el-input
            v-model="newFormInline.phone"
            clearable
            :placeholder="$t('system.phonePlaceholder')"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.userEmail')" prop="email">
          <el-input
            v-model="newFormInline.email"
            clearable
            :placeholder="$t('system.emailPlaceholder')"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.userSex')">
          <el-select
            v-model="newFormInline.sex"
            :placeholder="$t('system.sexPlaceholder')"
            class="w-full"
            clearable
          >
            <el-option
              v-for="(item, index) in sexOptions"
              :key="index"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.userDept')">
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
            :placeholder="$t('system.deptPlaceholder')"
          >
            <template #default="{ node, data }">
              <span>{{ data.name }}</span>
              <span v-if="!node.isLeaf"> ({{ data.children.length }}) </span>
            </template>
          </el-cascader>
        </el-form-item>
      </re-col>
      <re-col
        v-if="newFormInline.title === transformI18n('system.add')"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.userStatus')">
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
            :placeholder="$t('system.remarkPlaceholder')"
            type="textarea"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
