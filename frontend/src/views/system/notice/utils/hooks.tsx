import dayjs from "dayjs";
import editForm from "../form.vue";
import { message } from "@/utils/message";
import { addDialog } from "@/components/ReDialog";
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

// ─── 映射表 ───
const typeMap: Record<number, string> = {
  0: "系统通知",
  1: "业务通知",
  2: "公告"
};

const typeTagType: Record<number, string> = {
  0: "primary",
  1: "success",
  2: "warning"
};

const levelMap: Record<string, string> = {
  info: "普通",
  warning: "警告",
  important: "重要"
};

const levelTagType: Record<string, string> = {
  info: "info",
  warning: "warning",
  important: "danger"
};

const statusMap: Record<number, string> = {
  0: "草稿",
  1: "已发布"
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
    { label: "通知标题", prop: "title", minWidth: 160 },
    {
      label: "通知类型",
      prop: "type",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={typeTagType[row.type]}>
          {typeMap[row.type] ?? "未知"}
        </el-tag>
      )
    },
    {
      label: "通知级别",
      prop: "level",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={levelTagType[row.level] ?? "info"}>
          {levelMap[row.level] ?? row.level}
        </el-tag>
      )
    },
    {
      label: "通知状态",
      prop: "status",
      minWidth: 90,
      cellRenderer: ({ row }) => (
        <el-tag type={statusTagType[row.status]}>
          {statusMap[row.status] ?? "未知"}
        </el-tag>
      )
    },
    {
      label: "创建时间",
      prop: "created_at",
      minWidth: 170,
      formatter: ({ created_at }) =>
        dayjs(created_at).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      label: "操作",
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

  function openDialog(title = "新增", row?: FormItemProps) {
    const isAdd = title === "新增";
    addDialog({
      title: `${title}通知`,
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
          message(`${title}成功: ${curData.title}`, { type: "success" });
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
        message(`删除成功: ${row.title}`, { type: "success" });
        onSearch();
      }
    });
  }

  function handleBatchDelete() {
    if (selectedIds.value.length === 0) {
      message("请至少选择一条数据", { type: "warning" });
      return;
    }
    deleteNotice(selectedIds.value).then(res => {
      if (res.success) {
        message("批量删除成功", { type: "success" });
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
