import { ref, reactive, computed, onMounted } from "vue";
import { h } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance } from "element-plus";
import { addDialog } from "@/components/ReDialog";
import { transformI18n } from "@/plugins/i18n";
import {
  getSecurityPolicy,
  updateSecurityPolicy,
  getIPRules,
  addIPRule,
  updateIPRule,
  deleteIPRules
} from "@/api/settings";
import type { SecurityPolicy, IPRule } from "@/types/settings";
import IpRuleForm from "../form.vue";

export function useSecuritySettings() {
  // ─── 安全策略 ──────────────────────────────────────────────────

  const policyRef = ref<FormInstance>();
  const policyLoading = ref(false);

  const policyForm = reactive<SecurityPolicy>({
    min_password_length: 8,
    require_uppercase: true,
    require_lowercase: true,
    require_digit: true,
    require_special: false,
    password_history_count: 3,
    max_login_attempts: 5,
    lockout_duration_minutes: 30,
    captcha_enabled: true
  });

  const initialPolicy = ref<SecurityPolicy | null>(null);

  const policyChanged = computed(() => {
    if (!initialPolicy.value) return false;
    return JSON.stringify(policyForm) !== JSON.stringify(initialPolicy.value);
  });

  /** 获取安全策略 */
  const fetchPolicy = async () => {
    policyLoading.value = true;
    const { data } = await getSecurityPolicy().catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return { data: null };
    });
    if (data) {
      Object.assign(policyForm, data);
      initialPolicy.value = JSON.parse(JSON.stringify(data));
    }
    policyLoading.value = false;
  };

  /** 保存策略 */
  const savePolicy = async () => {
    policyLoading.value = true;
    const res = await updateSecurityPolicy(policyForm).catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return null;
    });
    policyLoading.value = false;
    if (res) {
      ElMessage.success(transformI18n("system.security.policySaveSuccess"));
      initialPolicy.value = JSON.parse(JSON.stringify(policyForm));
    }
  };

  // ─── IP 规则管理 ────────────────────────────────────────────────

  const ipLoading = ref(false);
  const ipRules = ref<IPRule[]>([]);
  const ipFormRef = ref();

  /** 表格列配置 */
  const ipColumns: TableColumnList = [
    {
      label: transformI18n("system.security.ipCidr"),
      prop: "ip_cidr",
      minWidth: 180
    },
    {
      label: transformI18n("system.security.ruleType"),
      prop: "rule_type",
      minWidth: 120,
      align: "center",
      cellRenderer: ({ row }) => (
        <el-tag
          type={row.rule_type === "whitelist" ? "success" : "danger"}
          size="small"
        >
          {row.rule_type === "whitelist"
            ? transformI18n("system.security.whitelist")
            : transformI18n("system.security.blacklist")}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.security.description"),
      prop: "description",
      minWidth: 200
    },
    {
      label: transformI18n("system.security.status"),
      prop: "is_active",
      width: 100,
      align: "center",
      cellRenderer: ({ row }) => (
        <el-tag type={row.is_active ? "success" : "info"} size="small">
          {row.is_active
            ? transformI18n("system.security.enabled")
            : transformI18n("system.security.disabled")}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.security.createdAt"),
      prop: "created_at",
      width: 180
    },
    {
      label: transformI18n("system.operation"),
      fixed: "right",
      width: 180,
      align: "center",
      slot: "operation"
    }
  ];

  /** 获取 IP 规则 */
  const fetchIPRules = async () => {
    ipLoading.value = true;
    const { data } = await getIPRules().catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return { data: [] };
    });
    ipRules.value = data || [];
    ipLoading.value = false;
  };

  /** 新增 IP 规则 */
  const handleAddIPRule = async (formData: Partial<IPRule>) => {
    if (!formData.ip_cidr) {
      ElMessage.warning(transformI18n("system.security.enterIpCidr"));
      return;
    }
    const res = await addIPRule({
      ip_cidr: formData.ip_cidr,
      rule_type: formData.rule_type as "whitelist" | "blacklist",
      description: formData.description || "",
      is_active: formData.is_active ?? true
    }).catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return null;
    });
    if (res) {
      ElMessage.success(transformI18n("system.security.ipRuleAddSuccess"));
      await fetchIPRules();
    }
  };

  /** 编辑 IP 规则 */
  const handleUpdateIPRule = async (formData: Partial<IPRule>) => {
    const res = await updateIPRule(formData as any).catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return null;
    });
    if (res) {
      ElMessage.success(transformI18n("system.security.ipRuleUpdateSuccess"));
      await fetchIPRules();
    }
  };

  /** 删除 IP 规则 */
  const handleDeleteIPRules = async (ids: string[]) => {
    await ElMessageBox.confirm(
      transformI18n("system.security.ipRuleDeleteConfirm"),
      transformI18n("system.confirm"),
      { type: "warning" }
    ).catch(() => null);
    const res = await deleteIPRules(ids).catch(() => {
      ElMessage.error(transformI18n("system.saveFail"));
      return null;
    });
    if (res) {
      ElMessage.success(transformI18n("system.deleteSuccess"));
      await fetchIPRules();
    }
  };

  /** 打开新增弹窗 */
  const openAddDialog = () => {
    addDialog({
      title: transformI18n("system.security.addRule"),
      props: {
        formInline: {
          ip_cidr: "",
          rule_type: "blacklist" as const,
          description: "",
          is_active: true
        }
      },
      width: "500px",
      draggable: true,
      closeOnClickModal: false,
      contentRenderer: ({ options }) =>
        h(IpRuleForm, { ref: ipFormRef, ...options.props }),
      beforeSure: (done, { closeLoading }) => {
        const curData = ipFormRef.value?.getFormData();
        if (!curData) {
          closeLoading();
          return;
        }
        handleAddIPRule(curData)
          .then(() => {
            done();
          })
          .catch(() => {
            closeLoading();
          });
      }
    });
  };

  /** 打开编辑弹窗 */
  const openEditDialog = (row: IPRule) => {
    addDialog({
      title: transformI18n("system.security.editRule"),
      props: {
        formInline: {
          id: row.id,
          ip_cidr: row.ip_cidr,
          rule_type: row.rule_type,
          description: row.description,
          is_active: row.is_active
        }
      },
      width: "500px",
      draggable: true,
      closeOnClickModal: false,
      contentRenderer: ({ options }) =>
        h(IpRuleForm, { ref: ipFormRef, ...options.props }),
      beforeSure: (done, { closeLoading }) => {
        const curData = ipFormRef.value?.getFormData();
        if (!curData) {
          closeLoading();
          return;
        }
        handleUpdateIPRule(curData)
          .then(() => {
            done();
          })
          .catch(() => {
            closeLoading();
          });
      }
    });
  };

  onMounted(() => {
    fetchPolicy();
    fetchIPRules();
  });

  return {
    policyRef,
    policyLoading,
    policyForm,
    policyChanged,
    savePolicy,
    ipLoading,
    ipRules,
    ipColumns,
    openAddDialog,
    openEditDialog,
    handleDeleteIPRules
  };
}
