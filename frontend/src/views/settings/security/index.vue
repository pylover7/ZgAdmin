<script setup lang="ts">
import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance } from "element-plus";
import { Lock, Key, Warning } from "@element-plus/icons-vue";
import {
  getSecurityPolicy,
  updateSecurityPolicy,
  getIPRules,
  addIPRule,
  updateIPRule,
  deleteIPRules
} from "@/api/settings";
import type { SecurityPolicy, IPRule } from "@/types/settings";

defineOptions({
  name: "SecuritySettings"
});

// ─── 安全策略 ──────────────────────────────────────────────────────

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

const fetchPolicy = async () => {
  try {
    policyLoading.value = true;
    const { data } = await getSecurityPolicy();
    if (data) {
      Object.assign(policyForm, data);
      initialPolicy.value = JSON.parse(JSON.stringify(data));
    }
  } catch (error) {
    console.error("获取安全策略失败:", error);
  } finally {
    policyLoading.value = false;
  }
};

const savePolicy = async () => {
  try {
    policyLoading.value = true;
    await updateSecurityPolicy(policyForm);
    ElMessage.success("安全策略保存成功");
    initialPolicy.value = JSON.parse(JSON.stringify(policyForm));
  } catch (error) {
    ElMessage.error("保存失败");
    console.error("保存安全策略失败:", error);
  } finally {
    policyLoading.value = false;
  }
};

// ─── IP 规则管理 ────────────────────────────────────────────────────

const ipLoading = ref(false);
const ipRules = ref<IPRule[]>([]);
const addDialogVisible = ref(false);
const editDialogVisible = ref(false);

const addForm = reactive({
  ip_cidr: "",
  rule_type: "blacklist" as "whitelist" | "blacklist",
  description: "",
  is_active: true
});

const editForm = reactive<Partial<IPRule>>({});

const fetchIPRules = async () => {
  try {
    ipLoading.value = true;
    const { data } = await getIPRules();
    ipRules.value = data || [];
  } catch (error) {
    console.error("获取IP规则失败:", error);
  } finally {
    ipLoading.value = false;
  }
};

const handleAddIPRule = async () => {
  if (!addForm.ip_cidr) {
    ElMessage.warning("请输入IP地址或CIDR");
    return;
  }
  try {
    await addIPRule({
      ip_cidr: addForm.ip_cidr,
      rule_type: addForm.rule_type,
      description: addForm.description,
      is_active: addForm.is_active
    });
    ElMessage.success("IP规则添加成功");
    addDialogVisible.value = false;
    resetAddForm();
    await fetchIPRules();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.msg || "添加失败");
  }
};

const handleEditIPRule = (row: IPRule) => {
  Object.assign(editForm, { ...row });
  editDialogVisible.value = true;
};

const handleUpdateIPRule = async () => {
  try {
    await updateIPRule(editForm as any);
    ElMessage.success("IP规则更新成功");
    editDialogVisible.value = false;
    await fetchIPRules();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.msg || "更新失败");
  }
};

const handleDeleteIPRules = async (ids: string[]) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${ids.length} 条IP规则吗？`,
      "确认删除",
      { type: "warning" }
    );
    await deleteIPRules(ids);
    ElMessage.success("删除成功");
    await fetchIPRules();
  } catch {
    // 用户取消
  }
};

const resetAddForm = () => {
  addForm.ip_cidr = "";
  addForm.rule_type = "blacklist";
  addForm.description = "";
  addForm.is_active = true;
};

const getRuleTypeTag = (type: string) => {
  return type === "whitelist" ? "success" : "danger";
};

const getRuleTypeLabel = (type: string) => {
  return type === "whitelist" ? "白名单" : "黑名单";
};

onMounted(() => {
  fetchPolicy();
  fetchIPRules();
});
</script>

<template>
  <div class="security-settings">
    <!-- 安全策略配置 -->
    <el-card
      v-loading="policyLoading"
      shadow="never"
      style="margin-bottom: 20px"
    >
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Lock /></el-icon>
            安全策略配置
          </span>
          <el-button
            type="primary"
            :disabled="!policyChanged"
            @click="savePolicy"
          >
            保存策略
          </el-button>
        </div>
      </template>

      <el-form
        ref="policyRef"
        :model="policyForm"
        label-width="160px"
        label-position="right"
      >
        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><Key /></el-icon>
            密码策略
          </div>
        </el-divider>

        <el-form-item label="最小密码长度">
          <el-input-number
            v-model="policyForm.min_password_length"
            :min="6"
            :max="32"
          />
        </el-form-item>

        <el-form-item label="需要大写字母">
          <el-switch v-model="policyForm.require_uppercase" />
        </el-form-item>

        <el-form-item label="需要小写字母">
          <el-switch v-model="policyForm.require_lowercase" />
        </el-form-item>

        <el-form-item label="需要数字">
          <el-switch v-model="policyForm.require_digit" />
        </el-form-item>

        <el-form-item label="需要特殊字符">
          <el-switch v-model="policyForm.require_special" />
        </el-form-item>

        <el-form-item label="密码历史检查">
          <el-input-number
            v-model="policyForm.password_history_count"
            :min="0"
            :max="24"
          />
          <span class="form-tip">最近 N 次密码不可重用，0 表示不检查</span>
        </el-form-item>

        <el-divider content-position="left">
          <div class="divider-title">
            <el-icon><Lock /></el-icon>
            登录保护
          </div>
        </el-divider>

        <el-form-item label="最大登录失败次数">
          <el-input-number
            v-model="policyForm.max_login_attempts"
            :min="3"
            :max="20"
          />
          <span class="form-tip">连续失败 N 次后锁定账号</span>
        </el-form-item>

        <el-form-item label="锁定时长(分钟)">
          <el-input-number
            v-model="policyForm.lockout_duration_minutes"
            :min="5"
            :max="1440"
          />
          <span class="form-tip">账号锁定后的等待时间</span>
        </el-form-item>

        <el-form-item label="启用登录验证码">
          <el-switch v-model="policyForm.captcha_enabled" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- IP 黑白名单 -->
    <el-card v-loading="ipLoading" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Warning /></el-icon>
            IP 黑白名单
          </span>
          <el-button type="primary" @click="addDialogVisible = true">
            新增规则
          </el-button>
        </div>
      </template>

      <el-alert
        title="白名单优先：如果存在白名单规则，则只有匹配白名单的 IP 才能访问；黑名单中的 IP 将被直接拒绝。"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />

      <el-table :data="ipRules" border stripe style="width: 100%">
        <el-table-column prop="ip_cidr" label="IP/CIDR" min-width="180" />
        <el-table-column
          prop="rule_type"
          label="类型"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getRuleTypeTag(row.rule_type)" size="small">
              {{ getRuleTypeLabel(row.rule_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" min-width="200" />
        <el-table-column
          prop="is_active"
          label="状态"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEditIPRule(row)">
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              @click="handleDeleteIPRules([row.id])"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="ipRules.length === 0" description="暂无IP规则" />
    </el-card>

    <!-- 新增 IP 规则对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增IP规则"
      width="500px"
      destroy-on-close
    >
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="IP/CIDR" required>
          <el-input
            v-model="addForm.ip_cidr"
            placeholder="如: 192.168.1.0/24 或 10.0.0.1"
          />
        </el-form-item>
        <el-form-item label="规则类型" required>
          <el-radio-group v-model="addForm.rule_type">
            <el-radio value="blacklist">黑名单</el-radio>
            <el-radio value="whitelist">白名单</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="addForm.description"
            type="textarea"
            :rows="2"
            placeholder="可选备注"
          />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="addForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddIPRule">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑 IP 规则对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑IP规则"
      width="500px"
      destroy-on-close
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="IP/CIDR">
          <el-input v-model="editForm.ip_cidr" />
        </el-form-item>
        <el-form-item label="规则类型">
          <el-radio-group v-model="editForm.rule_type">
            <el-radio value="blacklist">黑名单</el-radio>
            <el-radio value="whitelist">白名单</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateIPRule">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.security-settings {
  padding: 20px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .title {
      display: flex;
      gap: 8px;
      align-items: center;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  .divider-title {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 16px;
    font-weight: 500;
  }

  .form-tip {
    margin-left: 12px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  :deep(.el-card__body) {
    padding: 20px;
  }

  :deep(.el-divider) {
    margin: 24px 0;
  }
}
</style>
