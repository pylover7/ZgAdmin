import { reactive, ref } from "vue";
import { message } from "@/utils/message";
import { getMine, updateProfile } from "@/api/user";
import { transformI18n } from "@/plugins/i18n";
import type { FormInstance, FormRules } from "element-plus";

export function useProfile() {
  const loading = ref(false);
  const userInfoFormRef = ref<FormInstance>();

  const userInfos = reactive({
    nickname: "",
    email: "",
    phone: "",
    remark: ""
  });

  const rules = reactive<FormRules>({
    nickname: [
      {
        required: true,
        message: transformI18n("system.nicknameRequired"),
        trigger: "blur"
      }
    ],
    email: [
      {
        required: true,
        message: transformI18n("system.emailRequired"),
        trigger: "blur"
      }
    ]
  });

  function queryEmail(
    queryString: string,
    callback: (results: { value: string }[]) => void
  ) {
    const emailList = [
      { value: "@qq.com" },
      { value: "@126.com" },
      { value: "@163.com" }
    ];
    const queryList = emailList.map(item => ({
      value: queryString.split("@")[0] + item.value
    }));
    const results = queryString
      ? queryList.filter(
          item =>
            item.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
        )
      : queryList;
    callback(results);
  }

  const onSubmit = async (formEl: FormInstance | undefined) => {
    if (!formEl) return;
    const valid = await formEl.validate().catch(() => false);
    if (!valid) return;

    loading.value = true;
    const res = await updateProfile({
      nickname: userInfos.nickname,
      email: userInfos.email,
      phone: userInfos.phone,
      remark: userInfos.remark
    }).catch(() => null);
    loading.value = false;

    if (res !== null) {
      message(transformI18n("system.updateProfileSuccess"), {
        type: "success"
      });
    } else {
      message(transformI18n("system.updateProfileFail"), { type: "error" });
    }
  };

  async function loadProfile() {
    const res = await getMine();
    if (res?.data) {
      userInfos.nickname = res.data.nickname || "";
      userInfos.email = res.data.email || "";
      userInfos.phone = res.data.phone || "";
      userInfos.remark = res.data.remark || "";
    }
  }

  return {
    loading,
    userInfoFormRef,
    userInfos,
    rules,
    queryEmail,
    onSubmit,
    loadProfile
  };
}
