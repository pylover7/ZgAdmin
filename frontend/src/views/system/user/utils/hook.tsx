import "./reset.css";
import dayjs from "dayjs";
import roleForm from "../form/role.vue";
import editForm from "../form/index.vue";
import { zxcvbn } from "@zxcvbn-ts/core";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import userAvatar from "@/assets/user.jpg";
import { usePublicHooks } from "../../hooks";
import { addDialog } from "@/components/ReDialog";
import { $t } from "@/plugins/i18n";
import type { FormItemProps, RoleFormItemProps } from "../utils/types";
import {
  getKeyList,
  isAllEmpty,
  hideTextAtIndex,
  deviceDetection
} from "@pureadmin/utils";
import {
  getRoleIds,
  getDeptList,
  getUserList,
  getAllRoleList,
  addUser,
  deleteUser,
  updateUser,
  updateUserStatus
} from "@/api/system";
import { ElMessageBox } from "element-plus";
import { type Ref, h, ref, watch, computed, reactive, onMounted } from "vue";
import { paginationConf } from "@/config";
import type { PaginationProps } from "@pureadmin/table";

export function useUser(tableRef: Ref, treeRef: Ref) {
  const form = reactive({
    // 左侧部门树的id
    deptId: "",
    username: "",
    email: "",
    status: ""
  });
  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const switchLoadMap = ref({});
  const { switchStyle } = usePublicHooks();
  const higherDeptOptions = ref();
  const treeData = ref([]);
  const treeLoading = ref(true);
  const selectedNum = ref(0);
  const pagination = reactive<PaginationProps>({ ...paginationConf });
  const columns: TableColumnList = [
    {
      label: $t("system.select"),
      type: "selection",
      fixed: "left",
      reserveSelection: true
    },
    {
      label: "#",
      type: "index",
      width: 90
    },
    {
      label: $t("system.uploadAvatar"),
      prop: "avatar",
      cellRenderer: ({ row }) => (
        <el-image
          fit="cover"
          preview-teleported={true}
          src={row.avatar || userAvatar}
          preview-src-list={Array.of(row.avatar || userAvatar)}
          class="w-[24px] h-[24px] rounded-full align-middle"
        />
      ),
      width: 90
    },
    {
      label: $t("system.username"),
      prop: "username",
      minWidth: 130
    },
    {
      label: $t("system.nickname"),
      prop: "nickname",
      minWidth: 130
    },
    {
      label: $t("system.sex"),
      prop: "sex",
      minWidth: 90,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={row.sex === 0 ? "danger" : null}
          effect="plain"
        >
          {row.sex === 0 ? $t("system.female") : $t("system.male")}
        </el-tag>
      )
    },
    {
      label: $t("system.dept"),
      prop: "dept.name",
      minWidth: 90
    },
    {
      label: $t("system.phone"),
      prop: "phone",
      minWidth: 90,
      formatter: ({ phone }) => {
        if (!phone) return "-";
        return hideTextAtIndex(phone, { start: 3, end: 6 });
      }
    },
    {
      label: $t("system.status"),
      prop: "status",
      minWidth: 90,
      cellRenderer: scope => (
        <el-switch
          size={scope.props.size === "small" ? "small" : "default"}
          loading={switchLoadMap.value[scope.index]?.loading}
          v-model={scope.row.status}
          active-value={1}
          inactive-value={0}
          active-text={$t("system.enabled")}
          inactive-text={$t("system.disabled")}
          inline-prompt
          style={switchStyle.value}
          onChange={() => onChange(scope as any)}
        />
      )
    },
    {
      label: $t("system.createTime"),
      minWidth: 90,
      prop: "created_at",
      formatter: ({ createTime }) =>
        dayjs(createTime).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      label: $t("system.operation"),
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];
  const buttonClass = computed(() => {
    return [
      "h-[20px]!",
      "reset-margin",
      "text-gray-500!",
      "dark:text-white!",
      "dark:hover:text-primary!"
    ];
  });
  // 重置的新密码
  const pwdForm = reactive({
    newPwd: ""
  });
  // 当前密码强度（0-4）
  const curScore = ref();
  const roleOptions = ref([]);

  function onChange({ row, index }) {
    ElMessageBox.confirm(
      `${$t("system.confirm")}${row.status === 0 ? $t("system.disabled") : $t("system.enabled")} ${row.username}?`,
      $t("system.confirm"),
      {
        confirmButtonText: $t("system.confirm"),
        cancelButtonText: $t("system.cancel"),
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
        updateUserStatus({ id: row.id, status: row.status })
          .then(res => {
            if (res.success) {
              message($t("system.editSuccess"), { type: "success" });
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

  function handleUpdate(row) {
    console.log(row);
  }

  function handleDelete(row) {
    deleteUser([row.id]).then(() => {
      message(`${$t("system.deleteSuccess")}: ${row.username}`, {
        type: "success"
      });
      onSearch();
    });
  }

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
    const curSelected = tableRef.value.getTableRef().getSelectionRows();
    message(`${$t("system.deleteSuccess")}: ${getKeyList(curSelected, "id")}`, {
      type: "success"
    });
    tableRef.value.getTableRef().clearSelection();
    onSearch();
  }

  async function onSearch() {
    loading.value = true;
    const { data, total, pageSize, currentPage } = await getUserList(
      form.username,
      form.email,
      form.deptId,
      pagination.pageSize,
      pagination.currentPage
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
    form.deptId = "";
    treeRef.value.onTreeReset();
    onSearch();
  };

  function onTreeSelect({ id, selected }) {
    form.deptId = selected ? id : "";
    onSearch();
  }

  function formatHigherDeptOptions(treeList) {
    // 根据返回数据的status字段值判断追加是否禁用disabled字段，返回处理后的树结构，用于上级部门级联选择器的展示（实际开发中也是如此，不可能前端需要的每个字段后端都会返回，这时需要前端自行根据后端返回的某些字段做逻辑处理）
    if (!treeList || !treeList.length) return;
    const newTreeList = [];
    for (let i = 0; i < treeList.length; i++) {
      treeList[i].disabled = treeList[i].status === 0 ? true : false;
      formatHigherDeptOptions(treeList[i].children);
      newTreeList.push(treeList[i]);
    }
    return newTreeList;
  }

  function openDialog(title = $t("system.add"), row?: FormItemProps) {
    const isAdd = title === $t("system.add");
    addDialog({
      title: `${title}`,
      props: {
        formInline: {
          title,
          id: row?.id ?? "",
          higherDeptOptions: formatHigherDeptOptions(higherDeptOptions.value),
          parentId: row?.dept?.id ?? 0,
          nickname: row?.nickname ?? "",
          username: row?.username ?? "",
          password: row?.password ?? "",
          phone: row?.phone ?? null,
          email: row?.email ?? "",
          sex: row?.sex ?? 1,
          status: row?.status ?? 1,
          remark: row?.remark ?? ""
        }
      },
      width: "46%",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () => h(editForm, { ref: formRef, formInline: null }),
      beforeSure: (done, { options }) => {
        const FormRef = formRef.value.getRef();
        const curData = options.props.formInline as FormItemProps;
        function chores() {
          message(`${title}${$t("system.success")}: ${curData.username}`, {
            type: "success"
          });
          done(); // 关闭弹框
          onSearch(); // 刷新表格数据
        }
        FormRef.validate(valid => {
          if (valid) {
            console.log("curData", curData);
            // 表单规则校验通过
            if (isAdd) {
              delete curData.id;
              addUser(curData).then(res => {
                if (res.success) {
                  chores();
                } else {
                  message(res.msg, { type: "error" });
                }
              });
            } else {
              updateUser(curData).then(res => {
                if (res.success) {
                  chores();
                } else {
                  message(res.msg, { type: "error" });
                }
              });
            }
          }
        });
      }
    });
  }

  watch(
    pwdForm,
    ({ newPwd }) =>
      (curScore.value = isAllEmpty(newPwd) ? -1 : zxcvbn(newPwd).score)
  );

  /** 分配角色 */
  async function handleRole(row) {
    // 选中的角色列表
    const ids = (await getRoleIds({ userId: row.id })).data ?? [];
    addDialog({
      title: `${$t("system.assignRole")} - ${row.username}`,
      props: {
        formInline: {
          username: row?.username ?? "",
          nickname: row?.nickname ?? "",
          roleOptions: roleOptions.value ?? [],
          ids
        }
      },
      width: "400px",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () => h(roleForm),
      beforeSure: (done, { options }) => {
        const curData = options.props.formInline as RoleFormItemProps;
        console.log("curIds", curData.ids);
        // 根据实际业务使用curData.ids和row里的某些字段去调用修改角色接口即可
        done(); // 关闭弹框
      }
    });
  }

  onMounted(async () => {
    treeLoading.value = true;
    onSearch();

    // 归属部门
    const { data } = await getDeptList();
    higherDeptOptions.value = handleTree(data);
    treeData.value = handleTree(data);
    treeLoading.value = false;

    // 角色列表
    roleOptions.value = (await getAllRoleList()).data;
  });

  return {
    form,
    loading,
    columns,
    dataList,
    treeData,
    treeLoading,
    selectedNum,
    pagination,
    buttonClass,
    deviceDetection,
    onSearch,
    resetForm,
    onbatchDel,
    openDialog,
    onTreeSelect,
    handleUpdate,
    handleDelete,
    handleRole,
    handleSizeChange,
    onSelectionCancel,
    handleCurrentChange,
    handleSelectionChange
  };
}
