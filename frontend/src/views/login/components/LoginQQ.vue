<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "@/utils/message";
import Motion from "../utils/motion";
import { useUserStoreHook } from "@/store/modules/user";
import { getQQAuthUrl, qqLogin } from "@/api/user";
import { setToken } from "@/utils/auth";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import QQ from "~icons/ri/qq-fill";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const loading = ref(false);
const qrCodeUrl = ref("");

// 生成QQ登录二维码
const generateQQQRCode = async () => {
  try {
    const res = await getQQAuthUrl();
    if (res?.data) {
      qrCodeUrl.value = res.data.auth_url;
      // 将状态存储到sessionStorage用于回调验证
      sessionStorage.setItem("qq_login_state", res.data.state);
    }
  } catch (error) {
    console.error("获取QQ授权链接失败:", error);
    message(t("system.qqAuthUrlFail"), { type: "error" });
  }
};

// 处理QQ登录回调
const handleQQCallback = async () => {
  const { code, state } = route.query;

  if (!code || !state) {
    message(t("system.qqMissingParams"), { type: "error" });
    return;
  }

  // 验证state参数
  const storedState = sessionStorage.getItem("qq_login_state");
  if (state !== storedState) {
    message(t("system.qqStateVerifyFail"), { type: "error" });
    sessionStorage.removeItem("qq_login_state");
    return;
  }

  loading.value = true;
  useUserStoreHook()
    .loginByQQ({
      code: code as string,
      state: state as string
    })
    .then(res => {
      if (res.success) {
        message(t("login.pureLoginSuccess"), { type: "success" });
        router.push("/");
      } else {
        message(res.msg || t("system.qqLoginFail"), { type: "error" });
      }
    })
    .catch((error: any) => {
      console.error("QQ登录失败:", error);
      message(error.message || t("system.qqLoginFail"), { type: "error" });
    })
    .finally(() => {
      loading.value = false;
      sessionStorage.removeItem("qq_login_state");
    });
};

// 跳转到QQ授权页面
const redirectToQQ = () => {
  if (qrCodeUrl.value) {
    window.location.href = qrCodeUrl.value;
  } else {
    message(t("system.qqAuthUrlUnavailable"), { type: "error" });
  }
};

// 返回登录首页
const goBack = () => {
  useUserStoreHook().SET_CURRENTPAGE(0);
};

onMounted(() => {
  // 检查是否是QQ回调
  if (route.query.code && route.query.state) {
    handleQQCallback();
  } else {
    generateQQQRCode();
  }
});
</script>

<template>
  <div v-loading="loading" :element-loading-text="$t('system.loggingIn')">
    <Motion v-if="!route.query.code" class="-my-2">
      <div class="text-center mb-4">
        <h3 class="text-lg font-semibold mb-2">
          {{ $t("system.qqAccountLogin") }}
        </h3>
        <p class="text-gray-500 text-sm">{{ $t("system.qqSecureLogin") }}</p>
      </div>

      <!-- QQ登录按钮 -->
      <div class="qq-login-container">
        <el-button
          :icon="useRenderIcon(QQ)"
          type="primary"
          class="w-full! h-12! mb-4!"
          size="large"
          @click="redirectToQQ"
        >
          {{ $t("system.qqAccountLogin") }}
        </el-button>
      </div>

      <el-divider>
        <p class="text-gray-500 text-xs">{{ t("login.pureTip") }}</p>
      </el-divider>
    </Motion>

    <Motion :delay="150">
      <el-button class="w-full mt-4!" @click="goBack">
        {{ t("login.pureBack") }}
      </el-button>
    </Motion>
  </div>
</template>

<style scoped>
.qq-login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

:deep(.el-button) {
  font-weight: 500;
}
</style>
