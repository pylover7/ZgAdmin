import dayjs from "dayjs";
import { message } from "@/utils/message";
import { transformI18n } from "@/plugins/i18n";
import type { PaginationProps } from "@pureadmin/table";
import {
  getFileList,
  updateFile,
  deleteFile,
  previewFile,
  getSignedUrl,
  uploadFile,
  uploadBatch
} from "@/api/file";
import { reactive, ref, onMounted } from "vue";
import { paginationConf } from "@/config";
import { ElMessageBox } from "element-plus";
import type { FileFilter } from "./types";

// ─── 文件类型映射 ───
const fileTypeMap: Record<string, string> = {
  image: "system.file.typeImage",
  document: "system.file.typeDocument",
  video: "system.file.typeVideo",
  audio: "system.file.typeAudio",
  other: "system.file.typeOther"
};

const fileTypeTagType: Record<string, string> = {
  image: "primary",
  document: "success",
  video: "warning",
  audio: "danger",
  other: "info"
};

// ─── 文件图标映射 ───
const fileTypeIconMap: Record<string, string> = {
  image: "ep:picture",
  document: "ep:document",
  video: "ep:video-camera",
  audio: "ep:headset",
  other: "ep:document"
};

export function useFile() {
  const form = reactive<FileFilter>({
    name: "",
    file_type: null
  });

  const dataList = ref([]);
  const loading = ref(true);
  const selectedIds = ref<string[]>([]);
  const pagination = reactive<PaginationProps>({ ...paginationConf });
  const previewVisible = ref(false);
  const previewUrl = ref("");
  const previewName = ref("");

  const columns: TableColumnList = [
    { type: "selection", fixed: "left" },
    { label: "#", type: "index", minWidth: 60 },
    {
      label: transformI18n("system.file.name"),
      prop: "name",
      minWidth: 200,
      cellRenderer: ({ row }) => (
        <div class="flex items-center">
          <iconify-icon-offline
            icon={fileTypeIconMap[row.file_type] ?? "ep:document"}
            class="mr-2 text-lg"
          />
          <span>{row.name}</span>
        </div>
      )
    },
    {
      label: transformI18n("system.file.fileType"),
      prop: "file_type",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={fileTypeTagType[row.file_type] ?? "info"}>
          {transformI18n(fileTypeMap[row.file_type]) ?? row.file_type}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.file.size"),
      prop: "size_display",
      minWidth: 100
    },
    {
      label: transformI18n("system.file.uploader"),
      prop: "uploader_name",
      minWidth: 100
    },
    {
      label: transformI18n("system.createTime"),
      prop: "created_at",
      minWidth: 170,
      formatter: ({ created_at }) =>
        dayjs(created_at).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      label: transformI18n("system.operation"),
      fixed: "right",
      width: 240,
      slot: "operation"
    }
  ];

  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    onSearch();
  }

  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  function handleSelectionChange(val: any[]) {
    selectedIds.value = val.map(item => item.id);
  }

  async function onSearch() {
    loading.value = true;
    getFileList(
      { name: form.name || null, file_type: form.file_type },
      pagination.currentPage,
      pagination.pageSize
    )
      .then(({ data, total, pageSize, currentPage }) => {
        dataList.value = data;
        pagination.total = total;
        pagination.pageSize = pageSize;
        pagination.currentPage = currentPage;
      })
      .finally(() => {
        setTimeout(() => {
          loading.value = false;
        }, 300);
      });
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  };

  /** 重命名 */
  function handleRename(row) {
    ElMessageBox.prompt(
      transformI18n("system.file.newName"),
      transformI18n("system.file.rename"),
      {
        inputValue: row.name,
        confirmButtonText: transformI18n("buttons.pureConfirm"),
        cancelButtonText: transformI18n("system.cancel"),
        inputPattern: /\S+/,
        inputErrorMessage: transformI18n("system.file.nameRequired")
      }
    )
      .then(({ value }) => {
        updateFile({ id: row.id, name: value }).then(res => {
          if (res.success) {
            message(`${transformI18n("system.file.renameSuccess")}: ${value}`, {
              type: "success"
            });
            onSearch();
          }
        });
      })
      .catch(() => {});
  }

  /** 预览（仅图片，通过 JWT 获取 blob） */
  function handlePreview(row) {
    if (row.file_type !== "image") {
      // 非图片文件直接下载
      handleDownload(row);
      return;
    }
    previewFile(row.id).then(blob => {
      const url = URL.createObjectURL(blob as Blob);
      previewUrl.value = url;
      previewName.value = row.name;
      previewVisible.value = true;
    });
  }

  function closePreview() {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value);
    }
    previewVisible.value = false;
    previewUrl.value = "";
  }

  /** 下载（签名 URL） */
  function handleDownload(row) {
    getSignedUrl(row.id).then(res => {
      if (res.success && res.data?.url) {
        window.open(res.data.url, "_blank");
      }
    });
  }

  /** 删除 */
  function handleDelete(row) {
    deleteFile([row.id]).then(res => {
      if (res.success) {
        message(`${transformI18n("system.file.deleteSuccess")}: ${row.name}`, {
          type: "success"
        });
        onSearch();
      }
    });
  }

  /** 批量删除 */
  function handleBatchDelete() {
    if (selectedIds.value.length === 0) {
      message(transformI18n("system.file.atLeastOne"), { type: "warning" });
      return;
    }
    deleteFile(selectedIds.value).then(res => {
      if (res.success) {
        message(transformI18n("system.file.batchDeleteSuccess"), {
          type: "success"
        });
        selectedIds.value = [];
        onSearch();
      }
    });
  }

  /** 上传文件 */
  function handleUploadRequest(param): Promise<void> {
    const formData = new FormData();
    formData.append("file", param.file);
    return uploadFile(formData)
      .then(res => {
        if (res.success) {
          message(
            `${transformI18n("system.file.uploadSuccess")}: ${param.file.name}`,
            { type: "success" }
          );
          onSearch();
        } else {
          message(res.msg, { type: "warning" });
        }
      })
      .catch(() => {
        message(
          `${transformI18n("system.file.uploadFail")}: ${param.file.name}`,
          { type: "error" }
        );
      });
  }

  /** 批量上传 */
  function handleBatchUploadRequest(params) {
    const formData = new FormData();
    for (const file of params.files) {
      formData.append("files", file);
    }
    uploadBatch(formData)
      .then(res => {
        if (res.success) {
          const { success, fail } = res.data;
          if (fail.length > 0) {
            message(
              `${transformI18n("system.file.uploadPartial")}: ${success.length} ${transformI18n("system.file.uploadSuccess")}, ${fail.length} ${transformI18n("system.file.uploadFail")}`,
              { type: "warning" }
            );
          } else {
            message(
              `${transformI18n("system.file.uploadSuccess")}: ${success.length}`,
              { type: "success" }
            );
          }
          onSearch();
        }
      })
      .catch(() => {
        message(transformI18n("system.file.uploadFail"), { type: "error" });
      });
  }

  onMounted(() => {
    onSearch();
  });

  return {
    form,
    loading,
    columns,
    dataList,
    selectedIds,
    pagination,
    previewVisible,
    previewUrl,
    previewName,
    /** 搜索 */
    onSearch,
    /** 重置 */
    resetForm,
    /** 重命名 */
    handleRename,
    /** 预览 */
    handlePreview,
    /** 关闭预览 */
    closePreview,
    /** 下载 */
    handleDownload,
    /** 删除单条 */
    handleDelete,
    /** 批量删除 */
    handleBatchDelete,
    /** 上传 */
    handleUploadRequest,
    /** 批量上传 */
    handleBatchUploadRequest,
    handleSizeChange,
    handleCurrentChange,
    handleSelectionChange
  };
}
