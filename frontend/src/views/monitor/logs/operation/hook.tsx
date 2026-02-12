import dayjs from "dayjs";
import { message } from "@/utils/message";
import { getKeyList } from "@pureadmin/utils";
import {
  clearOperationLogs,
  deleteOperationLogs,
  getOperationLogsList
} from "@/api/system";
import type { PaginationProps } from "@pureadmin/table";
import { type Ref, reactive, ref, onMounted, computed } from "vue";
import { useDark } from "@pureadmin/utils";
import { paginationConf } from "@/config";

export function useRole(tableRef: Ref) {
  const { isDark } = useDark();

  const levelTagStyle = computed(() => {
    return (level: string) => {
      const styles: Record<string, Record<string, string>> = {
        info: isDark.value
          ? {
              "--el-tag-text-color": "#409eff",
              "--el-tag-bg-color": "#141414",
              "--el-tag-border-color": "#1a3a5c"
            }
          : {
              "--el-tag-text-color": "#1890ff",
              "--el-tag-bg-color": "#e6f7ff",
              "--el-tag-border-color": "#91d5ff"
            },
        warning: isDark.value
          ? {
              "--el-tag-text-color": "#faad14",
              "--el-tag-bg-color": "#2b2111",
              "--el-tag-border-color": "#594214"
            }
          : {
              "--el-tag-text-color": "#d48806",
              "--el-tag-bg-color": "#fffbe6",
              "--el-tag-border-color": "#ffe58f"
            },
        error: isDark.value
          ? {
              "--el-tag-text-color": "#ff4d4f",
              "--el-tag-bg-color": "#2b1316",
              "--el-tag-border-color": "#58191c"
            }
          : {
              "--el-tag-text-color": "#cf1322",
              "--el-tag-bg-color": "#fff1f0",
              "--el-tag-border-color": "#ffa39e"
            }
      };
      return styles[level] || styles.info;
    };
  });

  const levelTextMap: Record<string, string> = {
    info: "信息",
    warning: "警告",
    error: "重要"
  };

  const form = reactive({
    level: [],
    operationTime: null
  });
  const dataList = ref([]);
  const loading = ref(true);
  const selectedNum = ref(0);

  const pagination = reactive<PaginationProps>({ ...paginationConf });
  const columns: TableColumnList = [
    {
      label: "勾选列", // 如果需要表格多选，此处label必须设置
      type: "selection",
      fixed: "left",
      reserveSelection: true // 数据刷新后保留选项
    },
    {
      label: "序号",
      minWidth: 90,
      type: "index"
    },
    {
      label: "日志等级",
      prop: "level",
      minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={levelTagStyle.value(row.level)}>
          {levelTextMap[row.level] || row.level}
        </el-tag>
      )
    },
    {
      label: "操作人员",
      prop: "username",
      minWidth: 100
    },
    {
      label: "操作概要",
      prop: "message",
      minWidth: 140
    },
    {
      label: "操作时间",
      prop: "time",
      minWidth: 180,
      formatter: ({ operatingTime }) =>
        dayjs(operatingTime).format("YYYY-MM-DD HH:mm:ss")
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

  /** 当CheckBox选择项发生变化时会触发该事件 */
  function handleSelectionChange(val) {
    selectedNum.value = val.length;
    // 重置表格高度
    tableRef.value.setAdaptive();
  }

  /** 取消选择 */
  function onSelectionCancel() {
    selectedNum.value = 0;
    // 用于多选表格，清空用户的选择
    tableRef.value.getTableRef().clearSelection();
  }

  /** 批量删除 */
  function onbatchDel() {
    // 返回当前选中的行
    const curSelected = tableRef.value.getTableRef().getSelectionRows();
    deleteOperationLogs(getKeyList(curSelected, "id")).then(() => {
      message("删除成功", { type: "success" });
      tableRef.value.getTableRef().clearSelection();
      onSearch();
    });
  }

  /** 清空日志 */
  function clearAll() {
    // 根据实际业务，调用接口删除所有日志数据
    clearOperationLogs().then(() => {
      message("已删除所有日志数据", { type: "success" });
      onSearch();
    });
  }

  async function onSearch() {
    loading.value = true;
    const { data, total, currentPage, pageSize } = await getOperationLogsList(
      form.level,
      form.operationTime,
      pagination.currentPage,
      pagination.pageSize
    );
    dataList.value = data;
    pagination.total = total;
    pagination.pageSize = pageSize;
    pagination.currentPage = currentPage;

    setTimeout(() => {
      loading.value = false;
    }, 500);
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  };

  onMounted(() => {
    onSearch();
  });

  return {
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
  };
}
