import { ref, reactive, computed, onMounted } from "vue";
import { message } from "@/utils/message";
import { addDialog } from "@/components/ReDialog";
import { transformI18n } from "@/plugins/i18n";
import { updatePassword, updateProfile, getMine } from "@/api/user";
import type { FormRules } from "element-plus";

/** 列表项类型 */
type ListItem = {
  title: string;
  illustrate: string;
  button: string;
  action: "password" | "phone" | "question" | "email";
  disabled: boolean;
};

export function useAccountManagement() {
  const userInfo = ref({ phone: "", email: "" });

  function maskPhone(phone: string) {
    if (!phone || phone.length < 7) return phone;
    return phone.slice(0, 3) + "****" + phone.slice(-4);
  }

  function maskEmail(email: string) {
    if (!email || !email.includes("@")) return email;
    const [local, domain] = email.split("@");
    return local.slice(0, 1) + "***@" + domain;
  }

  onMounted(async () => {
    const res = await getMine().catch(() => ({ data: null }));
    if (res?.data) {
      userInfo.value.phone = res.data.phone || "";
      userInfo.value.email = res.data.email || "";
    }
  });

  const list = computed<ListItem[]>(() => [
    {
      title: transformI18n("system.accountPassword"),
      illustrate: transformI18n("system.passwordStrengthCurrent"),
      button: transformI18n("system.modify"),
      action: "password",
      disabled: false
    },
    {
      title: transformI18n("system.securityPhone"),
      illustrate: userInfo.value.phone
        ? `${transformI18n("system.boundPhone")}：${maskPhone(userInfo.value.phone)}`
        : transformI18n("system.bindPhoneTip"),
      button: transformI18n("system.modify"),
      action: "phone",
      disabled: false
    },
    {
      title: transformI18n("system.securityQuestion"),
      illustrate: transformI18n("system.securityQuestionTip"),
      button: transformI18n("system.modify"),
      action: "question",
      disabled: true
    },
    {
      title: transformI18n("system.backupEmail"),
      illustrate: userInfo.value.email
        ? `${transformI18n("system.boundEmail")}：${maskEmail(userInfo.value.email)}`
        : transformI18n("system.bindEmailTip"),
      button: transformI18n("system.modify"),
      action: "email",
      disabled: false
    }
  ]);

  // --- 修改密码弹窗 ---
  const pwdFormRef = ref();
  const pwdForm = reactive({
    current_password: "",
    new_password: "",
    confirm_password: ""
  });

  const validateConfirm = (_rule, value: string, callback) => {
    if (value !== pwdForm.new_password) {
      callback(new Error(transformI18n("system.pwdNotMatch")));
    } else {
      callback();
    }
  };

  const pwdRules = reactive<FormRules>({
    current_password: [
      {
        required: true,
        message: transformI18n("system.pleaseEnterCurrentPwd"),
        trigger: "blur"
      },
      {
        min: 8,
        max: 40,
        message: transformI18n("system.pwdLengthRange"),
        trigger: "blur"
      }
    ],
    new_password: [
      {
        required: true,
        message: transformI18n("system.pleaseEnterNewPwd"),
        trigger: "blur"
      },
      {
        min: 8,
        max: 40,
        message: transformI18n("system.pwdLengthRange"),
        trigger: "blur"
      }
    ],
    confirm_password: [
      {
        required: true,
        message: transformI18n("system.pleaseReenterNewPwd"),
        trigger: "blur"
      },
      { validator: validateConfirm, trigger: "blur" }
    ]
  });

  function openPasswordDialog() {
    pwdForm.current_password = "";
    pwdForm.new_password = "";
    pwdForm.confirm_password = "";

    addDialog({
      title: transformI18n("system.changePassword"),
      width: "400px",
      draggable: true,
      closeOnClickModal: false,
      contentRenderer: () => (
        <el-form
          ref={pwdFormRef}
          model={pwdForm}
          rules={pwdRules}
          label-width="100px"
        >
          <el-form-item
            label={transformI18n("system.currentPassword")}
            prop="current_password"
          >
            <el-input
              v-model={pwdForm.current_password}
              type="password"
              show-password
              placeholder={transformI18n("system.pleaseEnterCurrentPwd")}
            />
          </el-form-item>
          <el-form-item
            label={transformI18n("system.newPassword")}
            prop="new_password"
          >
            <el-input
              v-model={pwdForm.new_password}
              type="password"
              show-password
              placeholder={transformI18n("system.pleaseEnterNewPwd")}
            />
          </el-form-item>
          <el-form-item
            label={transformI18n("system.confirmNewPassword")}
            prop="confirm_password"
          >
            <el-input
              v-model={pwdForm.confirm_password}
              type="password"
              show-password
              placeholder={transformI18n("system.pleaseReenterNewPwd")}
            />
          </el-form-item>
        </el-form>
      ),
      beforeSure: (done, { closeLoading }) => {
        pwdFormRef.value?.validate(async (valid: boolean) => {
          if (!valid) {
            closeLoading();
            return;
          }
          const res = await updatePassword({
            current_password: pwdForm.current_password,
            new_password: pwdForm.new_password
          }).catch(() => {
            message(transformI18n("system.passwordModifyFail"), {
              type: "error"
            });
            return null;
          });
          if (res) {
            message(transformI18n("system.passwordModified"), {
              type: "success"
            });
            done();
          } else {
            closeLoading();
          }
        });
      }
    });
  }

  // --- 修改手机/邮箱弹窗 ---
  const fieldFormRef = ref();
  const fieldForm = reactive({ value: "" });
  let currentFieldAction: "phone" | "email" = "phone";

  const fieldRules = computed<FormRules>(() => ({
    value: [
      {
        required: true,
        message:
          currentFieldAction === "phone"
            ? transformI18n("system.pleaseEnterPhone")
            : transformI18n("system.pleaseEnterEmail"),
        trigger: "blur"
      },
      ...(currentFieldAction === "email"
        ? [
            {
              type: "email" as const,
              message: transformI18n("system.emailFormatError"),
              trigger: "blur" as const
            }
          ]
        : [
            {
              min: 7,
              max: 20,
              message: transformI18n("system.phoneFormatError"),
              trigger: "blur" as const
            }
          ])
    ]
  }));

  function openFieldDialog(action: "phone" | "email") {
    currentFieldAction = action;
    fieldForm.value =
      action === "phone" ? userInfo.value.phone : userInfo.value.email;

    const isPhone = action === "phone";
    const title = isPhone
      ? transformI18n("system.modifySecurityPhone")
      : transformI18n("system.modifyBackupEmail");

    addDialog({
      title,
      width: "400px",
      draggable: true,
      closeOnClickModal: false,
      contentRenderer: () => (
        <el-form
          ref={fieldFormRef}
          model={fieldForm}
          rules={fieldRules.value}
          label-width="100px"
        >
          <el-form-item
            label={
              isPhone
                ? transformI18n("system.phone")
                : transformI18n("system.email")
            }
            prop="value"
          >
            <el-input
              v-model={fieldForm.value}
              placeholder={
                isPhone
                  ? transformI18n("system.pleaseEnterNewPhone")
                  : transformI18n("system.pleaseEnterNewEmail")
              }
            />
          </el-form-item>
        </el-form>
      ),
      beforeSure: (done, { closeLoading }) => {
        fieldFormRef.value?.validate(async (valid: boolean) => {
          if (!valid) {
            closeLoading();
            return;
          }
          const res = await updateProfile({ [action]: fieldForm.value }).catch(
            () => {
              message(transformI18n("system.fieldModifyFail"), {
                type: "error"
              });
              return null;
            }
          );
          if (res) {
            userInfo.value[action] = fieldForm.value;
            message(transformI18n("system.fieldModified"), { type: "success" });
            done();
          } else {
            closeLoading();
          }
        });
      }
    });
  }

  function onClick(item: ListItem) {
    if (item.disabled) {
      message(transformI18n("system.notImplemented"), { type: "info" });
      return;
    }
    if (item.action === "password") {
      openPasswordDialog();
    } else if (item.action === "phone" || item.action === "email") {
      openFieldDialog(item.action);
    }
  }

  return {
    list,
    onClick
  };
}
