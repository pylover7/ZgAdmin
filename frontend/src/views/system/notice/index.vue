<script setup lang="ts">
import { ref, inject, type ComputedRef } from "vue";
import { useNotice } from "./utils/hooks";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import type { AdaptiveConfig } from "@/layout/hooks/useTableAdaptive";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "SystemNotice"
});

const formRef = ref();
const tableRef = ref();
const adaptiveConfig = inject<ComputedRef<AdaptiveConfig>>("adaptiveConfig");

const {
  form,
  loading,
  columns,
  dataList,
  selectedIds,
  pagination,
  onSearch,
  resetForm,
  openDialog,
  handleDelete,
  handleBatchDelete,
  handleSizeChange,
  handleCurrentChange,
  handleSelectionChange
} = useNotice();

function onFullscreen() {
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
      <el-form-item :label="$t('system.notice.title') + '：'" prop="title">
        <el-input
          v-model="form.title"
          :placeholder="$t('system.notice.enterTitle')"
          clearable
          class="w-45!"
        />
      </el-form-item>
      <el-form-item :label="$t('system.notice.type') + '：'" prop="type">
        <el-select
          v-model="form.type"
          :placeholder="$t('system.notice.selectType')"
          clearable
          class="w-45!"
        >
          <el-option :label="$t('system.notice.sysNotice')" :value="0" />
          <el-option :label="$t('system.notice.bizNotice')" :value="1" />
          <el-option :label="$t('system.notice.announce')" :value="2" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.notice.level') + '：'" prop="level">
        <el-select
          v-model="form.level"
          :placeholder="$t('system.notice.selectLevel')"
          clearable
          class="w-45!"
        >
          <el-option :label="$t('system.notice.info')" value="info" />
          <el-option :label="$t('system.notice.warn')" value="warning" />
          <el-option :label="$t('system.notice.important')" value="important" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.notice.status') + '：'" prop="status">
        <el-select
          v-model="form.status"
          :placeholder="$t('system.notice.selectStatus')"
          clearable
          class="w-45!"
          @change="onSearch"
        >
          <el-option :label="$t('system.notice.draft')" :value="0" />
          <el-option :label="$t('system.notice.published')" :value="1" />
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
      :title="$t('menus.zgNoticeSettings')"
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
          {{ $t("system.notice.publishNotice") }}
        </el-button>
        <el-button
          type="danger"
          :icon="useRenderIcon(Delete)"
          :disabled="selectedIds.length === 0"
          @click="handleBatchDelete"
        >
          {{ $t("system.batchDelete") }}
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
          :loading="loading"
          :size="size"
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
        >
          <template #operation="{ row, size }">
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
