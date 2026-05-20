<script setup lang="ts">
import { reactive, ref } from "vue";
import { message } from "@/utils/message";
import { getMine, updateProfile } from "@/api/user";
import type { FormInstance, FormRules } from "element-plus";
import { deviceDetection } from "@pureadmin/utils";

defineOptions({
  name: "Profile"
});

const loading = ref(false);
const userInfoFormRef = ref<FormInstance>();

const userInfos = reactive({
  nickname: "",
  email: "",
  phone: "",
  remark: ""
});

const rules = reactive<FormRules>({
  nickname: [{ required: true, message: "昵称必填", trigger: "blur" }],
  email: [{ required: true, message: "邮箱必填", trigger: "blur" }]
});

function queryEmail(queryString, callback) {
  const emailList = [
    { value: "@qq.com" },
    { value: "@126.com" },
    { value: "@163.com" }
  ];
  let results = [];
  let queryList = [];
  emailList.map(item =>
    queryList.push({ value: queryString.split("@")[0] + item.value })
  );
  results = queryString
    ? queryList.filter(
        item =>
          item.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
      )
    : queryList;
  callback(results);
}

const onSubmit = async (formEl: FormInstance) => {
  if (!formEl) return;
  await formEl.validate(async (valid, fields) => {
    if (valid) {
      loading.value = true;
      try {
        await updateProfile({
          nickname: userInfos.nickname,
          email: userInfos.email,
          phone: userInfos.phone,
          remark: userInfos.remark
        });
        message("更新信息成功", { type: "success" });
      } catch {
        message("更新信息失败", { type: "error" });
      } finally {
        loading.value = false;
      }
    } else {
      console.log("error submit!", fields);
    }
  });
};

getMine().then(res => {
  if (res?.data) {
    userInfos.nickname = res.data.nickname || "";
    userInfos.email = res.data.email || "";
    userInfos.phone = res.data.phone || "";
    userInfos.remark = res.data.remark || "";
  }
});
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">个人信息</h3>
    <el-form
      ref="userInfoFormRef"
      label-position="top"
      :rules="rules"
      :model="userInfos"
    >
      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="userInfos.nickname" placeholder="请输入昵称" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-autocomplete
          v-model="userInfos.email"
          :fetch-suggestions="queryEmail"
          :trigger-on-focus="false"
          placeholder="请输入邮箱"
          clearable
          class="w-full"
        />
      </el-form-item>
      <el-form-item label="联系电话">
        <el-input
          v-model="userInfos.phone"
          placeholder="请输入联系电话"
          clearable
        />
      </el-form-item>
      <el-form-item label="简介">
        <el-input
          v-model="userInfos.remark"
          placeholder="请输入简介"
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
        更新信息
      </el-button>
    </el-form>
  </div>
</template>
