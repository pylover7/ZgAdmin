import dayjs from "dayjs";
import { message } from "@/utils/message";
import { getKeyList } from "@pureadmin/utils";
import { clearLoginLogs, deleteLoginLogs, getLoginLogsList } from "@/api/system";
import { usePublicHooks, formatDateTimeRange } from "@/views/system/hooks";
import { transformI18n } from "@/plugins/i18n";
import { type Ref, reactive, ref, onMounted } from "vue";
import { paginationConf } from "@/config";
import type { PaginationProps } from "@pureadmin/table";

export function useRole(tableRef: Ref) {
  const { tagStyle } = usePublicHooks();

  const form = reactive({
    username: "",
    level: "",
    loginTime: null
  });
  const dataList = ref([]);
  const loading = ref(true);
  const selectedNum = ref(0);

  const pagination = reactive<PaginationProps>({ ...paginationConf });
  const columns: TableColumnList = [
    { label: transformI18n("system.select"), type: "selection", fixed: "left", reserveSelection: true },
    { label: "#", minWidth: 90, type: "index" },
    { label: transformI18n("system.username"), prop: "username", minWidth: 100 },
    { label: transformI18n("system.loginIp"), prop: "ip", minWidth: 140 },
    { label: transformI18n("system.loginAddress"), prop: "address", minWidth: 140 },
    { label: transformI18n("system.loginSystem"), prop: "system", minWidth: 100 },
    { label: transformI18n("system.loginBrowser"), prop: "browser", minWidth: 100 },
    {
      label: transformI18n("system.status"), prop: "level", minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.level == "success" ? 1 : 0)}>
          {row.level === "success" ? transformI18n("system.success") : transformI18n("system.fail")}
        </el-tag>
      )
    },
    { label: transformI18n("system.loginBehavior"), prop: "behavior", minWidth: 100 },
    { label: transformI18n("system.loginTime"), prop: "time", minWidth: 180,
      formatter: ({ time }) => dayjs(time).format("YYYY-MM-DD HH:mm:ss") }
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
    console.log("当前选中行：", getKeyList(curSelected, "id"));
    deleteLoginLogs(getKeyList(curSelected, "id")).then(() => {
      message(transformI18n("system.deleteSuccess"), { type: "success" });
      tableRef.value.getTableRef().clearSelection();
      onSearch();
    });
  }

  /** 清空日志 */
  function clearAll() {
    clearLoginLogs().then(() => {
      message(transformI18n("system.clearLog") + transformI18n("system.success"), { type: "success" });
      onSearch();
    });
  }

  async function onSearch() {
    loading.value = true;
    const { data, total, pageSize, currentPage } = await getLoginLogsList(
      form.username,
      form.level,
      formatDateTimeRange(form.loginTime),
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
