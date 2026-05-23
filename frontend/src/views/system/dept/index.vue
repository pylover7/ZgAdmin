<script setup lang="ts">
import { ref, inject, computed, type ComputedRef } from "vue";
import { useDept } from "./utils/hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import type { AdaptiveConfig } from "@/layout/hooks/useTableAdaptive";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "SystemDept"
});

const formRef = ref();
const tableRef = ref();
const injectConfig = inject<ComputedRef<AdaptiveConfig>>("adaptiveConfig");
// 部门管理是树形表格，无分页器，需要减去分页器高度预算（~32px + margin 16px×2 = 64px）
const adaptiveConfig = computed<AdaptiveConfig>(() => ({
  offsetBottom: (injectConfig?.value?.offsetBottom ?? 108) - 64,
  fixHeader: injectConfig?.value?.fixHeader ?? true,
  timeout: injectConfig?.value?.timeout ?? 60,
  zIndex: injectConfig?.value?.zIndex ?? 3
}));
const {
  form,
  loading,
  columns,
  dataList,
  onSearch,
  resetForm,
  openDialog,
  handleDelete,
  handleSelectionChange
} = useDept();

function onFullscreen() {
  // 重置表格高度
  tableRef.value.setAdaptive();
}
</script>

<template>
  <div class="main">
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
    >
      <el-form-item :label="$t('system.deptName') + '：'" prop="name">
        <el-input
          v-model="form.name"
          :placeholder="$t('system.pleaseInput') + $t('system.deptName')"
          clearable
          class="w-45!"
        />
      </el-form-item>
      <el-form-item :label="$t('system.status') + '：'" prop="status">
        <el-select
          v-model="form.status"
          :placeholder="$t('system.pleaseSelect') + $t('system.status')"
          clearable
          class="w-45!"
          @change="onSearch"
        >
          <el-option :label="$t('system.enabled')" :value="1" />
          <el-option :label="$t('system.disabled')" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :icon="useRenderIcon('ri/search-line')"
          :loading="loading"
          @click="onSearch"
        >
          {{ $t("system.search") }}
        </el-button>
        <el-button :icon="useRenderIcon(Refresh)" @click="resetForm(formRef)">
          {{ $t("system.reset") }}
        </el-button>
      </el-form-item>
    </el-form>

    <PureTableBar
      :title="$t('menus.pureDept')"
      :columns="columns"
      :tableRef="tableRef?.getTableRef()"
      @refresh="onSearch"
      @fullscreen="onFullscreen"
    >
      <template #buttons>
        <el-button
          type="primary"
          :icon="useRenderIcon(AddFill)"
          @click="openDialog()"
        >
          {{ $t("system.add") }}
        </el-button>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <pure-table
          ref="tableRef"
          adaptive
          :adaptiveConfig="adaptiveConfig"
          align-whole="center"
          row-key="id"
          showOverflowTooltip
          table-layout="auto"
          default-expand-all
          :loading="loading"
          :size="size"
          :data="dataList"
          :columns="dynamicColumns"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @selection-change="handleSelectionChange"
        >
          <template #operation="{ row }">
            <el-button
              class="reset-margin"
              link
              type="primary"
              :size="size"
              :icon="useRenderIcon(EditPen)"
              @click="openDialog($t('system.edit'), row)"
            >
              {{ $t("system.edit") }}
            </el-button>
            <el-button
              class="reset-margin"
              link
              type="primary"
              :size="size"
              :icon="useRenderIcon(AddFill)"
              @click="openDialog($t('system.add'), { parentId: row.id } as any)"
            >
              {{ $t("system.add") }}
            </el-button>
            <el-popconfirm
              :title="$t('system.deleteConfirm')"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
                  class="reset-margin"
                  link
                  type="primary"
                  :size="size"
                  :icon="useRenderIcon(Delete)"
                >
                  {{ $t("system.delete") }}
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </pure-table>
      </template>
    </PureTableBar>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}
</style>
