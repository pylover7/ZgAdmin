<script setup lang="ts">
import { ref, reactive } from "vue";
import { message } from "@/utils/message";
import { updatePassword } from "@/api/user";
import { deviceDetection } from "@pureadmin/utils";
import type { FormInstance, FormRules } from "element-plus";

defineOptions({
  name: "AccountManagement"
});

const dialogVisible = ref(false);
const pwdFormRef = ref<FormInstance>();
const pwdLoading = ref(false);

const pwdForm = reactive({
  current_password: "",
  new_password: "",
  confirm_password: ""
});

const validateConfirm = (_rule, value: string, callback) => {
  if (value !== pwdForm.new_password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const pwdRules = reactive<FormRules>({
  current_password: [
    { required: true, message: "请输入当前密码", trigger: "blur" },
    { min: 8, max: 40, message: "密码长度为8-40位", trigger: "blur" }
  ],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 8, max: 40, message: "密码长度为8-40位", trigger: "blur" }
  ],
  confirm_password: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    { validator: validateConfirm, trigger: "blur" }
  ]
});

const list = ref([
  {
    title: "账户密码",
    illustrate: "当前密码强度：强",
    button: "修改",
    action: "password",
    disabled: false
  },
  {
    title: "密保手机",
    illustrate: "绑定手机后可通过手机号找回密码",
    button: "修改",
    action: "phone",
    disabled: true
  },
  {
    title: "密保问题",
    illustrate: "未设置密保问题，密保问题可有效保护账户安全",
    button: "修改",
    action: "question",
    disabled: true
  },
  {
    title: "备用邮箱",
    illustrate: "已绑定邮箱可用于找回密码",
    button: "修改",
    action: "email",
    disabled: true
  }
]);

function onClick(item) {
  if (item.disabled) {
    message("暂未实现", { type: "info" });
    return;
  }
  if (item.action === "password") {
    dialogVisible.value = true;
  }
}

async function onSubmitPwd(formEl: FormInstance) {
  if (!formEl) return;
  await formEl.validate(async valid => {
    if (valid) {
      pwdLoading.value = true;
      try {
        await updatePassword({
          current_password: pwdForm.current_password,
          new_password: pwdForm.new_password
        });
        message("密码修改成功", { type: "success" });
        dialogVisible.value = false;
        pwdForm.current_password = "";
        pwdForm.new_password = "";
        pwdForm.confirm_password = "";
      } catch {
        message("密码修改失败", { type: "error" });
      } finally {
        pwdLoading.value = false;
      }
    }
  });
}
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">账户管理</h3>
    <div v-for="(item, index) in list" :key="index">
      <div class="flex items-center">
        <div class="flex-1">
          <p>{{ item.title }}</p>
          <el-text class="mx-1" type="info">{{ item.illustrate }}</el-text>
        </div>
        <el-button
          :type="item.disabled ? 'info' : 'primary'"
          text
          :disabled="item.disabled"
          @click="onClick(item)"
        >
          {{ item.button }}
        </el-button>
      </div>
      <el-divider />
    </div>

    <el-dialog v-model="dialogVisible" title="修改密码" width="400px">
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="100px"
      >
        <el-form-item label="当前密码" prop="current_password">
          <el-input
            v-model="pwdForm.current_password"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="pwdForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="pwdForm.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="pwdLoading"
          @click="onSubmitPwd(pwdFormRef)"
        >
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.el-divider--horizontal {
  border-top: 0.1px var(--el-border-color) var(--el-border-style);
}
</style>
