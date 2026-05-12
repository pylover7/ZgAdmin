import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { ElMessageBox } from "element-plus";
import { usePublicHooks } from "../../hooks";
import { $t, transformI18n } from "@/plugins/i18n";
import { addDialog } from "@/components/ReDialog";
import type { FormItemProps } from "../utils/types";
import type { PaginationProps } from "@pureadmin/table";
import { getKeyList, deviceDetection } from "@pureadmin/utils";
import {
  addRole,
  getMenuList,
  getRoleList,
  getRoleMenuIds,
  updateRole,
  updateRoleAuth,
  updateRoleStatus
} from "@/api/system";
import { type Ref, reactive, ref, onMounted, h, watch } from "vue";
import { paginationConf } from "@/config";

export function useRole(treeRef: Ref) {
  const form = reactive({
    name: "",
    code: "",
    status: ""
  });
  const curRow = ref();
  const formRef = ref();
  const dataList = ref([]);
  const treeIds = ref([]);
  const treeData = ref([]);
  const isShow = ref(false);
  const loading = ref(true);
  const treeSearchValue = ref();
  const switchLoadMap = ref({});
  const isExpandAll = ref(false);
  const isSelectAll = ref(false);
  const { switchStyle } = usePublicHooks();
  const treeProps = {
    value: "id",
    label: "title",
    children: "children"
  };
  const pagination = reactive<PaginationProps>({ ...paginationConf });
  const columns: TableColumnList = [
    { label: "#", type: "index", minWidth: 60 },
    { label: transformI18n("system.roleName"), prop: "name" },
    { label: transformI18n("system.roleCode"), prop: "code" },
    {
      label: transformI18n("system.status"),
      cellRenderer: scope => (
        <el-switch
          size={scope.props.size === "small" ? "small" : "default"}
          loading={switchLoadMap.value[scope.index]?.loading}
          v-model={scope.row.status}
          active-value={1}
          inactive-value={0}
          active-text={transformI18n("system.enabled")}
          inactive-text={transformI18n("system.disabled")}
          inline-prompt
          style={switchStyle.value}
          onChange={() => onChange(scope as any)}
        />
      ),
      minWidth: 90
    },
    { label: transformI18n("system.remark"), prop: "remark", minWidth: 160 },
    {
      label: transformI18n("system.createTime"),
      prop: "createTime",
      minWidth: 160,
      formatter: ({ createTime }) =>
        dayjs(createTime).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      label: transformI18n("system.operation"),
      fixed: "right",
      width: 210,
      slot: "operation"
    }
  ];

  function onChange({ row, index }) {
    const action =
      row.status === 0
        ? transformI18n("system.disabled")
        : transformI18n("system.enabled");
    ElMessageBox.confirm(
      `${transformI18n("system.confirm")} ${action} 【${row.name}】?`,
      transformI18n("system.confirm"),
      {
        confirmButtonText: transformI18n("system.confirm"),
        cancelButtonText: transformI18n("system.cancel"),
        type: "warning",
        dangerouslyUseHTMLString: true,
        draggable: true
      }
    )
      .then(() => {
        switchLoadMap.value[index] = Object.assign(
          {},
          switchLoadMap.value[index],
          { loading: true }
        );
        updateRoleStatus({ id: row.id, status: row.status })
          .then(res => {
            if (res.success) {
              message(
                `${action} ${transformI18n("system.role")}【${row.name}】${transformI18n("system.success")}`,
                { type: "success" }
              );
            } else {
              row.status === 0 ? (row.status = 1) : (row.status = 0);
            }
          })
          .finally(() => {
            switchLoadMap.value[index] = Object.assign(
              {},
              switchLoadMap.value[index],
              { loading: false }
            );
          });
      })
      .catch(() => {
        row.status === 0 ? (row.status = 1) : (row.status = 0);
      });
  }

  function handleDelete(row) {
    message(`${transformI18n("system.deleteSuccess")}: ${row.name}`, {
      type: "success"
    });
    onSearch();
  }

  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    onSearch();
  }

  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  function handleSelectionChange(val) {
    console.log("handleSelectionChange", val);
  }

  async function onSearch() {
    loading.value = true;
    const { data, total, pageSize, currentPage } = await getRoleList(
      form.name,
      form.code,
      form.status,
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

  function openDialog(
    title = transformI18n("system.add"),
    row?: FormItemProps
  ) {
    const isAdd = title === transformI18n("system.add");
    addDialog({
      title: `${title}`,
      props: {
        formInline: {
          name: row?.name ?? "",
          code: row?.code ?? "",
          remark: row?.remark ?? ""
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
            `${title}${transformI18n("system.success")}: ${curData.name}`,
            { type: "success" }
          );
          done();
          onSearch();
        }
        FormRef.validate(valid => {
          if (valid) {
            if (isAdd) {
              addRole(curData).then(res => {
                if (res.success) {
                  chores();
                }
              });
            } else {
              updateRole(curData).then(res => {
                if (res.success) {
                  chores();
                }
              });
            }
          }
        });
      }
    });
  }

  /** 菜单权限 */
  async function handleMenu(row?: any) {
    const { id } = row;
    if (id) {
      curRow.value = row;
      isShow.value = true;
      const { data } = await getRoleMenuIds({ id });
      treeRef.value.setCheckedKeys(data);
      console.log("data", data);
      console.log("treeRef.value", treeRef.value);
    } else {
      curRow.value = null;
      isShow.value = false;
    }
  }

  /** 高亮当前权限选中行 */
  function rowStyle({ row: { id } }) {
    return {
      cursor: "pointer",
      background: id === curRow.value?.id ? "var(--el-fill-color-light)" : ""
    };
  }

  /** 菜单权限-保存 */
  function handleSave() {
    const { id, name } = curRow.value;
    // 根据用户 id 调用实际项目中菜单权限修改接口
    updateRoleAuth({ id, menuIds: treeRef.value.getCheckedKeys() }).then(
      res => {
        if (res.success) {
          message(
            `${transformI18n("system.role")}【${name}】${transformI18n("system.roleAuth")}${transformI18n("system.editSuccess")}`,
            { type: "success" }
          );
        }
      }
    );
  }

  /** 数据权限 可自行开发 */
  // function handleDatabase() {}

  const onQueryChanged = (query: string) => {
    treeRef.value!.filter(query);
  };

  const filterMethod = (query: string, node) => {
    return transformI18n(node.title)!.includes(query);
  };

  onMounted(async () => {
    onSearch();
    const { data } = await getMenuList();
    treeIds.value = getKeyList(data, "id");
    treeData.value = handleTree(data);
  });

  watch(isExpandAll, val => {
    val
      ? treeRef.value.setExpandedKeys(treeIds.value)
      : treeRef.value.setExpandedKeys([]);
  });

  watch(isSelectAll, val => {
    val
      ? treeRef.value.setCheckedKeys(treeIds.value)
      : treeRef.value.setCheckedKeys([]);
  });

  return {
    form,
    isShow,
    curRow,
    loading,
    columns,
    rowStyle,
    dataList,
    treeData,
    treeProps,
    pagination,
    isExpandAll,
    isSelectAll,
    treeSearchValue,
    // buttonClass,
    onSearch,
    resetForm,
    openDialog,
    handleMenu,
    handleSave,
    handleDelete,
    filterMethod,
    transformI18n,
    onQueryChanged,
    // handleDatabase,
    handleSizeChange,
    handleCurrentChange,
    handleSelectionChange
  };
}
