<script setup lang="ts">
import { ref, inject, type ComputedRef } from "vue";
import { useRole } from "./hook";
import { getPickerShortcuts } from "../../utils";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import type { AdaptiveConfig } from "@/layout/hooks/useTableAdaptive";

import Delete from "~icons/ep/delete";
import Refresh from "~icons/ep/refresh";

defineOptions({
  name: "LoginLog"
});

const formRef = ref();
const tableRef = ref();
const adaptiveConfig = inject<ComputedRef<AdaptiveConfig>>("adaptiveConfig");

const {
  form,
  loading,
  columns,
  dataList,
  pagination,
  selectedNum,
  onSearch,
  clearAll,
  resetForm,
  onbatchDel,
  handleSizeChange,
  onSelectionCancel,
  handleCurrentChange,
  handleSelectionChange
} = useRole(tableRef);
</script>

<template>
  <div class="main">
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
    >
      <el-form-item :label="$t('system.username')" prop="username">
        <el-input
          v-model="form.username"
          :placeholder="$t('system.pleaseInput') + $t('system.username')"
          clearable
          class="w-37.5!"
        />
      </el-form-item>
      <el-form-item :label="$t('system.status')" prop="level">
        <el-select
          v-model="form.level"
          :placeholder="$t('system.pleaseSelect')"
          clearable
          class="w-37.5!"
        >
          <el-option :label="$t('system.success')" value="success" />
          <el-option :label="$t('system.fail')" value="fail" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.loginTime')" prop="loginTime">
        <el-date-picker
          v-model="form.loginTime"
          :shortcuts="getPickerShortcuts()"
          type="datetimerange"
          range-separator="—"
          :start-placeholder="$t('system.startTime')"
          :end-placeholder="$t('system.endTime')"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :icon="useRenderIcon('ri:search-line')"
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
      :title="$t('system.loginLog')"
      :columns="columns"
      @refresh="onSearch"
    >
      <template #buttons>
        <el-popconfirm
          :title="$t('system.clearLogConfirm')"
          @confirm="clearAll"
        >
          <template #reference>
            <el-button type="danger" :icon="useRenderIcon(Delete)">
              {{ $t("system.clearLog") }}
            </el-button>
          </template>
        </el-popconfirm>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <div
          v-if="selectedNum > 0"
          v-motion-fade
          class="bg-(--el-fill-color-light) w-full h-11.5 mb-2 pl-4 flex items-center"
        >
          <div class="flex-auto">
            <span
              style="font-size: var(--el-font-size-base)"
              class="text-[rgba(42,46,54,0.5)] dark:text-[rgba(220,220,242,0.5)]"
            >
              {{ selectedNum }} {{ $t("system.selected") }}
            </span>
            <el-button type="primary" text @click="onSelectionCancel">
              {{ $t("system.cancel") }}
            </el-button>
          </div>
          <el-popconfirm
            :title="$t('system.deleteConfirm')"
            @confirm="onbatchDel"
          >
            <template #reference>
              <el-button type="danger" text class="mr-1!">{{
                $t("system.batchDelete")
              }}</el-button>
            </template>
          </el-popconfirm>
        </div>
        <pure-table
          ref="tableRef"
          row-key="id"
          align-whole="center"
          table-layout="auto"
          :loading="loading"
          :size="size"
          adaptive
          :adaptiveConfig="adaptiveConfig"
          :data="dataList"
          :columns="dynamicColumns"
          :pagination="{ ...pagination, size }"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @selection-change="handleSelectionChange"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        />
      </template>
    </PureTableBar>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-dropdown-menu__item i) {
  margin: 0;
}
</style>
