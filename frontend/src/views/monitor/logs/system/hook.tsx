import dayjs from "dayjs";
import { message } from "@/utils/message";
import type { PaginationProps } from "@pureadmin/table";
import { transformI18n } from "@/plugins/i18n";
import { type Ref, reactive, ref, onMounted } from "vue";
import { getKeyList } from "@pureadmin/utils";
import {
  getSystemLogsList,
  deleteSystemLogs,
  clearSystemLogs
} from "@/api/system";
import {
  usePublicHooks,
  levelTextMap,
  formatDateTimeRange
} from "@/views/system/hooks";
import { paginationConf } from "@/config";

export function useRole(tableRef: Ref) {
  const { levelTagStyle } = usePublicHooks();

  const form = reactive({
    module: "",
    operationTime: null
  });
  const dataList = ref([]);
  const loading = ref(true);
  const selectedNum = ref(0);

  const pagination = reactive<PaginationProps>({ ...paginationConf });

  const selectOpt = [
    { label: "系统管理", value: "系统管理" },
    { label: "系统", value: "系统" },
    { label: "数据库", value: "数据库" }
  ];

  const columns: TableColumnList = [
    {
      label: transformI18n("system.select"),
      type: "selection",
      fixed: "left",
      reserveSelection: true
    },
    {
      type: "index",
      label: "#",
      minWidth: 60
    },
    {
      label: "所属模块",
      prop: "module",
      minWidth: 100
    },
    {
      label: "日志级别",
      prop: "level",
      minWidth: 90,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={levelTagStyle.value(row.level)}>
          {levelTextMap[row.level] || row.level}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.logMessage"),
      prop: "message",
      minWidth: 200,
      align: "left"
    },
    {
      label: transformI18n("system.operationTime"),
      prop: "time",
      minWidth: 180,
      formatter: ({ time }) => dayjs(time).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      label: "操作",
      fixed: "right",
      width: 80,
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

  function handleSelectionChange(val) {
    selectedNum.value = val.length;
    tableRef.value.setAdaptive();
  }

  function onSelectionCancel() {
    selectedNum.value = 0;
    tableRef.value.getTableRef().clearSelection();
  }

  function onbatchDel() {
    const curSelected = tableRef.value.getTableRef().getSelectionRows();
    deleteSystemLogs(getKeyList(curSelected, "id")).then(() => {
      message("已删除选中日志数据", {
        type: "success"
      });
      selectedNum.value = 0;
      tableRef.value.getTableRef().clearSelection();
      onSearch();
    });
  }

  function clearAll() {
    clearSystemLogs().then(() => {
      message(
        transformI18n("system.clearLog") + transformI18n("system.success"),
        {
          type: "success"
        }
      );
      onSearch();
    });
  }

  async function onSearch() {
    loading.value = true;
    const { data, total, pageSize, currentPage } = await getSystemLogsList(
      form.module,
      formatDateTimeRange(form.operationTime),
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
    selectOpt,
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
