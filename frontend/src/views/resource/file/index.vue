<script setup lang="ts">
import { ref, inject, type ComputedRef } from "vue";
import { useFile } from "./utils/hooks";
import { transformI18n } from "@/plugins/i18n";
import { PureTableBar } from "@/components/RePureTableBar";
import { message } from "@/utils/message";
import type { AdaptiveConfig } from "@/layout/hooks/useTableAdaptive";

const adaptiveConfig = inject<ComputedRef<AdaptiveConfig>>("adaptiveConfig");

const {
  form,
  loading,
  columns,
  dataList,
  pagination,
  previewVisible,
  previewUrl,
  previewName,
  onSearch,
  resetForm,
  handleRename,
  handlePreview,
  closePreview,
  handleDownload,
  handleDelete,
  handleBatchDelete,
  handleUploadRequest,
  handleSizeChange,
  handleCurrentChange,
  handleSelectionChange
} = useFile();

const formRef = ref();
const uploadCollapsed = ref(true);
const MAX_UPLOAD_SIZE = 10 * 1024 * 1024; // 10MB，与服务端限制保持一致
const UPLOAD_LIMIT = 10;

const fileTypeOptions = [
  { label: transformI18n("system.file.typeImage"), value: "image" },
  { label: transformI18n("system.file.typeDocument"), value: "document" },
  { label: transformI18n("system.file.typeVideo"), value: "video" },
  { label: transformI18n("system.file.typeAudio"), value: "audio" },
  { label: transformI18n("system.file.typeOther"), value: "other" }
];

/** 客户端文件大小校验，避免大文件浪费带宽后才被服务端拒绝 */
function beforeUpload(file: File) {
  if (file.size > MAX_UPLOAD_SIZE) {
    message(
      `${transformI18n("system.file.uploadFail")}: ${file.name} (>10MB)`,
      { type: "warning" }
    );
    return false;
  }
  return true;
}

function handleExceed() {
  message(
    `${transformI18n("system.file.uploadFail")}: max ${UPLOAD_LIMIT} files`,
    {
      type: "warning"
    }
  );
}
</script>

<template>
  <div>
    <div class="flex-bc bg-bg_color px-4 pt-3 pb-2">
      <el-form ref="formRef" :inline="true" :model="form">
        <el-form-item :label="transformI18n('system.file.name')" prop="name">
          <el-input
            v-model="form.name"
            :placeholder="transformI18n('system.file.namePlaceholder')"
            clearable
            @keyup.enter="onSearch"
          />
        </el-form-item>
        <el-form-item
          :label="transformI18n('system.file.fileType')"
          prop="file_type"
        >
          <el-select
            v-model="form.file_type"
            :placeholder="transformI18n('system.file.fileTypePlaceholder')"
            clearable
            class="!w-[150px]"
          >
            <el-option
              v-for="item in fileTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">
            {{ transformI18n("system.search") }}
          </el-button>
          <el-button @click="resetForm(formRef)">
            {{ transformI18n("system.reset") }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <PureTableBar
      :title="transformI18n('menus.zgFileManager')"
      :columns="columns"
      @refresh="onSearch"
    >
      <template #buttons>
        <el-button type="primary" @click="uploadCollapsed = !uploadCollapsed">
          {{ transformI18n("system.file.upload") }}
          <iconify-icon-offline
            :icon="uploadCollapsed ? 'ep:arrow-down' : 'ep:arrow-up'"
            class="ml-1"
          />
        </el-button>
        <el-button type="danger" @click="handleBatchDelete">
          {{ transformI18n("system.file.batchDelete") }}
        </el-button>
      </template>

      <template v-slot="{ size, dynamicColumns }">
        <div v-if="!uploadCollapsed" class="p-4 border-b border-gray-200">
          <el-upload
            drag
            multiple
            :limit="UPLOAD_LIMIT"
            :show-file-list="false"
            :http-request="handleUploadRequest"
            :before-upload="beforeUpload"
            :on-exceed="handleExceed"
            accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.md,.mp4,.avi,.mov,.mp3,.wav"
          >
            <template #default>
              <div class="el-upload__text">
                {{ transformI18n("system.file.dragTip") }}
                <em>{{ transformI18n("system.file.clickUpload") }}</em>
              </div>
            </template>
          </el-upload>
        </div>

        <pure-table
          row-key="id"
          adaptive
          :adaptiveConfig="adaptiveConfig"
          :loading="loading"
          :data="dataList"
          :columns="dynamicColumns"
          :size="size"
          :pagination="pagination"
          :paginationSmall="size === 'small'"
          :header-cell-style="{
            background: 'var(--el-table-row-hover-bg-color)',
            color: 'var(--el-text-color-primary)'
          }"
          @selection-change="handleSelectionChange"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        >
          <template #operation="{ row, size }">
            <el-button
              :size="size"
              type="primary"
              link
              @click="handlePreview(row)"
            >
              {{ transformI18n("system.file.preview") }}
            </el-button>
            <el-button
              :size="size"
              type="primary"
              link
              @click="handleDownload(row)"
            >
              {{ transformI18n("system.file.download") }}
            </el-button>
            <el-button
              :size="size"
              type="primary"
              link
              @click="handleRename(row)"
            >
              {{ transformI18n("system.file.rename") }}
            </el-button>
            <el-popconfirm
              :title="transformI18n('system.file.confirmDelete')"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button :size="size" type="danger" link>
                  {{ transformI18n("system.file.delete") }}
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </pure-table>
      </template>
    </PureTableBar>

    <!-- 图片预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewName"
      width="60%"
      @close="closePreview"
    >
      <div class="flex-c">
        <img
          :src="previewUrl"
          :alt="previewName"
          class="max-w-full max-h-[70vh]"
          @error="previewUrl = ''"
        />
      </div>
    </el-dialog>
  </div>
</template>
