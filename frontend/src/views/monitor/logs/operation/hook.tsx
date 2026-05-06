import dayjs from "dayjs";
import { message } from "@/utils/message";
import { getKeyList } from "@pureadmin/utils";
import {
  clearOperationLogs,
  deleteOperationLogs,
  getOperationLogsList
} from "@/api/system";
import type { PaginationProps } from "@pureadmin/table";
import { type Ref, reactive, ref, onMounted } from "vue";
import {
  usePublicHooks,
  levelTextMap,
  formatDateTimeRange
} from "@/views/system/hooks";
import { transformI18n } from "@/plugins/i18n";
import { paginationConf } from "@/config";

export function useRole(tableRef: Ref) {
  const { levelTagStyle } = usePublicHooks();

  const form = reactive({
    level: [],
    operationTime: null
  });
  const dataList = ref([]);
  const loading = ref(true);
  const selectedNum = ref(0);

  const pagination = reactive<PaginationProps>({ ...paginationConf });
  const columns: TableColumnList = [
    { label: transformI18n("system.select"), type: "selection", fixed: "left", reserveSelection: true },
    { label: "#", minWidth: 90, type: "index" },
    { label: transformI18n("system.logLevel"), prop: "level", minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={levelTagStyle.value(row.level)}>
          {levelTextMap[row.level] || row.level}
        </el-tag>
      )
    },
    { label: transformI18n("system.operationUser"), prop: "username", minWidth: 100 },
    { label: transformI18n("system.logMessage"), prop: "message", minWidth: 140 },
    { label: transformI18n("system.operationTime"), prop: "time", minWidth: 180,
      formatter: ({ operatingTime }) => dayjs(operatingTime).format("YYYY-MM-DD HH:mm:ss") }
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
      message(transformI18n("system.deleteSuccess"), { type: "success" });
      tableRef.value.getTableRef().clearSelection();
      onSearch();
    });
  }

  /** 清空日志 */
  function clearAll() {
    // 根据实际业务，调用接口删除所有日志数据
    clearOperationLogs().then(() => {
      message(transformI18n("system.clearLog") + transformI18n("system.success"), { type: "success" });
      onSearch();
    });
  }

  async function onSearch() {
    loading.value = true;
    const { data, total, currentPage, pageSize } = await getOperationLogsList(
      form.level,
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
