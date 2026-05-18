import dayjs from "dayjs";
import editForm from "../form.vue";
import { message } from "@/utils/message";
import { addDialog } from "@/components/ReDialog";
import { transformI18n } from "@/plugins/i18n";
import type { FormItemProps } from "./types";
import type { PaginationProps } from "@pureadmin/table";
import { deviceDetection } from "@pureadmin/utils";
import {
  addNotice,
  getNoticeList,
  updateNotice,
  deleteNotice
} from "@/api/notice";
import { reactive, ref, onMounted, h } from "vue";
import { paginationConf } from "@/config";

// ─── 映射表（值存 i18n key） ───
const typeMap: Record<number, string> = {
  0: "system.notice.sysNotice",
  1: "system.notice.bizNotice",
  2: "system.notice.announce"
};

const typeTagType: Record<number, string> = {
  0: "primary",
  1: "success",
  2: "warning"
};

const levelMap: Record<string, string> = {
  info: "system.notice.info",
  warning: "system.notice.warn",
  important: "system.notice.important"
};

const levelTagType: Record<string, string> = {
  info: "info",
  warning: "warning",
  important: "danger"
};

const statusMap: Record<number, string> = {
  0: "system.notice.draft",
  1: "system.notice.published"
};

const statusTagType: Record<number, string> = {
  0: "info",
  1: "success"
};

export function useNotice() {
  const form = reactive({
    title: "",
    type: null as number | null,
    level: null as string | null,
    status: null as number | null
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const selectedIds = ref<string[]>([]);
  const pagination = reactive<PaginationProps>({ ...paginationConf });

  const columns: TableColumnList = [
    { type: "selection", fixed: "left" },
    { label: "#", type: "index", minWidth: 60 },
    {
      label: transformI18n("system.notice.title"),
      prop: "title",
      minWidth: 160
    },
    {
      label: transformI18n("system.notice.type"),
      prop: "type",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={typeTagType[row.type]}>
          {transformI18n(typeMap[row.type]) ??
            transformI18n("system.notice.type")}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.notice.level"),
      prop: "level",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={levelTagType[row.level] ?? "info"}>
          {transformI18n(levelMap[row.level]) ?? row.level}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.notice.status"),
      prop: "status",
      minWidth: 90,
      cellRenderer: ({ row }) => (
        <el-tag type={statusTagType[row.status]}>
          {transformI18n(statusMap[row.status]) ??
            transformI18n("system.notice.status")}
        </el-tag>
      )
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
      width: 160,
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
    try {
      const { data, total, pageSize, currentPage } = await getNoticeList(
        form.title,
        form.type,
        form.level ?? "",
        form.status,
        pagination.currentPage,
        pagination.pageSize
      );
      dataList.value = data;
      pagination.total = total;
      pagination.pageSize = pageSize;
      pagination.currentPage = currentPage;
    } finally {
      setTimeout(() => {
        loading.value = false;
      }, 500);
    }
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  };

  function openDialog(
    title = transformI18n("system.add"),
    row?: FormItemProps
  ) {
    const isAdd = title === transformI18n("system.add");
    addDialog({
      title: `${title}${transformI18n("system.notice.noticeLabel")}`,
      props: {
        formInline: {
          id: row?.id ?? "",
          title: row?.title ?? "",
          content: row?.content ?? "",
          type: row?.type ?? 0,
          level: row?.level ?? "info",
          status: row?.status ?? 0
        }
      },
      width: "40%",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () => h(editForm, { ref: formRef, formInline: null }),
      beforeSure: (done, { options }) => {
        const FormRef = formRef.value.getRef();
        const curData = options.props.formInline as FormItemProps;
        function chores() {
          message(
            `${title}${transformI18n("system.success")}: ${curData.title}`,
            { type: "success" }
          );
          done();
          onSearch();
        }
        FormRef.validate(valid => {
          if (valid) {
            if (isAdd) {
              delete curData.id;
              addNotice(curData).then(res => {
                if (res.success) {
                  chores();
                } else {
                  message(res.msg, { type: "warning" });
                }
              });
            } else {
              updateNotice(curData).then(res => {
                if (res.success) {
                  chores();
                } else {
                  message(res.msg, { type: "warning" });
                }
              });
            }
          }
        });
      }
    });
  }

  function handleDelete(row) {
    deleteNotice([row.id]).then(res => {
      if (res.success) {
        message(
          `${transformI18n("system.notice.deleteSuccess")}: ${row.title}`,
          { type: "success" }
        );
        onSearch();
      }
    });
  }

  function handleBatchDelete() {
    if (selectedIds.value.length === 0) {
      message(transformI18n("system.notice.atLeastOne"), { type: "warning" });
      return;
    }
    deleteNotice(selectedIds.value).then(res => {
      if (res.success) {
        message(transformI18n("system.notice.batchDeleteSuccess"), {
          type: "success"
        });
        selectedIds.value = [];
        onSearch();
      }
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
    /** 搜索 */
    onSearch,
    /** 重置 */
    resetForm,
    /** 新增、编辑通知 */
    openDialog,
    /** 删除单条 */
    handleDelete,
    /** 批量删除 */
    handleBatchDelete,
    handleSizeChange,
    handleCurrentChange,
    handleSelectionChange
  };
}
