<script setup lang="ts">
import { useI18n } from "vue-i18n";
import Motion from "./utils/motion";
import { useRouter, useRoute } from "vue-router";
import { message } from "@/utils/message";
import { loginRules } from "./utils/rule";
import TypeIt from "@/components/ReTypeit";
import { debounce } from "@pureadmin/utils";
import { useNav } from "@/layout/hooks/useNav";
import { useEventListener } from "@vueuse/core";
import type { FormInstance } from "element-plus";
import { $t, transformI18n } from "@/plugins/i18n";
import { operates } from "./utils/enums";
import { useLayout } from "@/layout/hooks/useLayout";
import LoginUpdate from "./components/LoginUpdate.vue";
import LoginWeChat from "./components/LoginWeChat.vue";
import LoginQQ from "./components/LoginQQ.vue";
import { useUserStoreHook } from "@/store/modules/user";
import { initRouter, getTopMenu } from "@/router/utils";
import { bg, avatar, illustration } from "./utils/static";
import { ref, toRaw, reactive, watch, computed, onMounted } from "vue";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { useTranslationLang } from "@/layout/hooks/useTranslationLang";
import { useDataThemeChange } from "@/layout/hooks/useDataThemeChange";
import { getLoginMethods, getCaptcha, getSecurityConfig } from "@/api/user";
import type { loginType } from "@/types/login";
import { getConfig } from "@/config";

import dayIcon from "@/assets/svg/day.svg?component";
import darkIcon from "@/assets/svg/dark.svg?component";
import globalization from "@/assets/svg/globalization.svg?component";
import Lock from "~icons/ri/lock-fill";
import Check from "~icons/ep/check";
import User from "~icons/ri/user-3-fill";
import Info from "~icons/ri/information-line";
import Keyhole from "~icons/ri/shield-keyhole-line";

defineOptions({
  name: "Login"
});

const imgCode = ref("");
const captchaKey = ref("");
const captchaImage = ref("");
const captchaEnabled = ref(true);
const loginDay = ref(7);
const router = useRouter();
const route = useRoute();
const loading = ref(false);
const checked = ref(false);
const disabled = ref(false);
const ruleFormRef = ref<FormInstance>();
const currentPage = computed(() => {
  return useUserStoreHook().currentPage;
});
const loginMethods = ref<loginType>({
  qq: { enabled: false },
  wechat: { enabled: false }
});
const TITLE = getConfig("Title");
const COPYRIGHT = getConfig("Copyright");
const ICP = getConfig("Icp");

// 计算可用的登录方式（根据配置过滤）
const availableOperates = computed(() => {
  return operates.filter((_, index) => {
    if (index === 0) {
      return loginMethods.value.qq.enabled;
    }
    if (index === 1) {
      return loginMethods.value.wechat.enabled;
    }
    return false;
  });
});

const { t } = useI18n();
const { initStorage } = useLayout();
initStorage();
const { dataTheme, overallStyle, dataThemeChange } = useDataThemeChange();
dataThemeChange(overallStyle.value);
const { title, getDropdownItemStyle, getDropdownItemClass } = useNav();
const { locale, translationCh, translationEn } = useTranslationLang();

const ruleForm = reactive({
  username: "admin",
  password: "admin123456",
  verifyCode: ""
});

/** 获取服务端验证码 */
const refreshCaptcha = async () => {
  try {
    const res = await getCaptcha();
    if (res.success && res.data) {
      captchaKey.value = res.data.captcha_key;
      captchaImage.value = res.data.captcha_image;
      ruleForm.verifyCode = "";
    }
  } catch (error) {
    console.error("获取验证码失败:", error);
  }
};

const onLogin = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate(valid => {
    if (valid) {
      loading.value = true;
      useUserStoreHook()
        .loginByUsername({
          username: ruleForm.username,
          password: ruleForm.password,
          captcha_key: captchaEnabled.value ? captchaKey.value : undefined,
          captcha_code: captchaEnabled.value ? ruleForm.verifyCode : undefined
        })
        .then(res => {
          if (res.success) {
            return initRouter().then(() => {
              disabled.value = true;
              router
                .push(getTopMenu(true).path)
                .then(() => {
                  message(t("login.pureLoginSuccess"), { type: "success" });
                })
                .finally(() => (disabled.value = false));
            });
          } else {
            message(res.msg || t("login.pureLoginFail"), { type: "error" });
            if (captchaEnabled.value) refreshCaptcha();
          }
        })
        .catch(err => {
          const msg = err?.response?.data?.msg || t("login.pureLoginFail");
          message(msg, { type: "error" });
          if (captchaEnabled.value) refreshCaptcha();
        })
        .finally(() => (loading.value = false));
    }
  });
};

const immediateDebounce: any = debounce(
  formRef => onLogin(formRef),
  1000,
  true
);

useEventListener(document, "keydown", ({ code }) => {
  if (
    ["Enter", "NumpadEnter"].includes(code) &&
    !disabled.value &&
    !loading.value
  )
    immediateDebounce(ruleFormRef.value);
});

watch(checked, bool => {
  useUserStoreHook().SET_ISREMEMBERED(bool);
});
watch(loginDay, value => {
  useUserStoreHook().SET_LOGINDAY(value);
});

// 获取登录方式配置 & 安全配置 & 验证码
onMounted(async () => {
  if (route.path === "/login/qq/callback") {
    useUserStoreHook().SET_CURRENTPAGE(1);
  }
  try {
    const [methodsRes, securityRes] = await Promise.all([
      getLoginMethods(),
      getSecurityConfig()
    ]);
    if (methodsRes.success && methodsRes.data) {
      loginMethods.value = methodsRes.data;
    }
    if (securityRes.success && securityRes.data) {
      captchaEnabled.value = securityRes.data.captcha_enabled;
    }
    if (captchaEnabled.value) {
      await refreshCaptcha();
    }
  } catch (error) {
    console.error("初始化登录配置失败:", error);
  }
});
</script>

<template>
  <div class="select-none">
    <img :src="bg" class="wave" />
    <div class="flex-c absolute right-5 top-3">
      <!-- 主题 -->
      <el-switch
        v-model="dataTheme"
        inline-prompt
        :active-icon="dayIcon"
        :inactive-icon="darkIcon"
        @change="dataThemeChange"
      />
      <!-- 国际化 -->
      <el-dropdown trigger="click">
        <globalization
          class="hover:text-primary hover:bg-transparent! size-5 ml-1.5 cursor-pointer outline-hidden duration-300"
        />
        <template #dropdown>
          <el-dropdown-menu class="translation">
            <el-dropdown-item
              :style="getDropdownItemStyle(locale, 'zh')"
              :class="['dark:text-white!', getDropdownItemClass(locale, 'zh')]"
              @click="translationCh"
            >
              <IconifyIconOffline
                v-show="locale === 'zh'"
                class="check-zh"
                :icon="Check"
              />
              简体中文
            </el-dropdown-item>
            <el-dropdown-item
              :style="getDropdownItemStyle(locale, 'en')"
              :class="['dark:text-white!', getDropdownItemClass(locale, 'en')]"
              @click="translationEn"
            >
              <span v-show="locale === 'en'" class="check-en">
                <IconifyIconOffline :icon="Check" />
              </span>
              English
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <div class="login-container">
      <div class="img">
        <component :is="toRaw(illustration)" />
      </div>
      <div class="login-box">
        <div class="login-form">
          <avatar class="avatar" />
          <Motion>
            <h2 class="outline-hidden">
              <TypeIt
                :options="{ strings: [title], cursor: false, speed: 100 }"
              />
            </h2>
          </Motion>

          <el-form
            v-if="currentPage === 0"
            ref="ruleFormRef"
            :model="ruleForm"
            :rules="loginRules"
            size="large"
          >
            <Motion :delay="100">
              <el-form-item
                :rules="[
                  {
                    required: true,
                    message: transformI18n($t('login.pureUsernameReg')),
                    trigger: 'blur'
                  }
                ]"
                prop="username"
              >
                <el-input
                  v-model="ruleForm.username"
                  clearable
                  :placeholder="t('login.pureUsername')"
                  :prefix-icon="useRenderIcon(User)"
                />
              </el-form-item>
            </Motion>

            <Motion :delay="150">
              <el-form-item prop="password">
                <el-input
                  v-model="ruleForm.password"
                  clearable
                  show-password
                  :placeholder="t('login.purePassword')"
                  :prefix-icon="useRenderIcon(Lock)"
                />
              </el-form-item>
            </Motion>

            <Motion :delay="200">
              <el-form-item v-if="captchaEnabled" prop="verifyCode">
                <el-input
                  v-model="ruleForm.verifyCode"
                  clearable
                  :placeholder="t('login.pureVerifyCode')"
                  :prefix-icon="useRenderIcon(Keyhole)"
                >
                  <template v-slot:append>
                    <img
                      :src="captchaImage"
                      alt="captcha"
                      style="
                        height: 36px;
                        cursor: pointer;
                        border-radius: 0 4px 4px 0;
                      "
                      title="点击刷新验证码"
                      @click="refreshCaptcha"
                    />
                  </template>
                </el-input>
              </el-form-item>
            </Motion>

            <Motion :delay="250">
              <el-form-item>
                <div class="w-full h-5 flex-bc">
                  <el-checkbox v-model="checked">
                    <span class="flex">
                      <select
                        v-model="loginDay"
                        :style="{
                          width: loginDay < 10 ? '10px' : '16px',
                          outline: 'none',
                          background: 'none',
                          appearance: 'none',
                          border: 'none'
                        }"
                      >
                        <option value="1">1</option>
                        <option value="7">7</option>
                        <option value="30">30</option>
                      </select>
                      {{ t("login.pureRemember") }}
                      <IconifyIconOffline
                        v-tippy="{
                          content: t('login.pureRememberInfo'),
                          placement: 'top'
                        }"
                        :icon="Info"
                        class="ml-1"
                      />
                    </span>
                  </el-checkbox>
                  <el-button
                    link
                    type="primary"
                    @click="useUserStoreHook().SET_CURRENTPAGE(4)"
                  >
                    {{ t("login.pureForget") }}
                  </el-button>
                </div>
                <el-button
                  class="w-full mt-4!"
                  size="default"
                  type="primary"
                  :loading="loading"
                  :disabled="disabled"
                  @click="onLogin(ruleFormRef)"
                >
                  {{ t("login.pureLogin") }}
                </el-button>
              </el-form-item>
            </Motion>

            <Motion v-if="availableOperates.length > 0" :delay="300">
              <el-form-item>
                <div class="w-full h-5 flex-bc">
                  <el-button
                    v-for="(item, index) in availableOperates"
                    :key="index"
                    :icon="useRenderIcon(item.icon)"
                    class="w-full mt-4!"
                    size="default"
                    @click="useUserStoreHook().SET_CURRENTPAGE(index + 1)"
                  >
                    {{ t(item.title) }}
                  </el-button>
                </div>
              </el-form-item>
            </Motion>
          </el-form>

          <!-- QQ登录 -->
          <LoginQQ v-if="currentPage === 1" />
          <!-- 微信登录 -->
          <LoginWeChat v-if="currentPage === 2" />
          <!-- 忘记密码 -->
          <LoginUpdate v-if="currentPage === 3" />
        </div>
      </div>
    </div>
    <div
      class="w-full flex-c absolute bottom-3 text-sm text-[rgba(0,0,0,0.6)] dark:text-[rgba(220,220,242,0.8)]"
    >
      <span v-if="COPYRIGHT">{{ COPYRIGHT }}</span>
      <span v-else>
        Copyright © 2025-present
        <a
          class="hover:text-primary!"
          href="https://cnb.cool/pylover/Tools/ZgAdmin"
          target="_blank"
        >
          &nbsp;{{ TITLE }}
        </a>
      </span>
      <span v-if="ICP" class="ml-2">
        <a
          class="hover:text-primary!"
          href="https://beian.miit.gov.cn/"
          target="_blank"
        >
          {{ ICP }}
        </a>
      </span>
    </div>
  </div>
</template>

<style scoped>
@import url("@/style/login.css");
</style>

<style lang="scss" scoped>
:deep(.el-input-group__append, .el-input-group__prepend) {
  padding: 0;
}

.translation {
  ::v-deep(.el-dropdown-menu__item) {
    padding: 5px 40px;
  }

  .check-zh {
    position: absolute;
    left: 20px;
  }

  .check-en {
    position: absolute;
    left: 20px;
  }
}
</style>
