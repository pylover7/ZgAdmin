import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { $t } from "@/plugins/i18n";
import { message } from "@/utils/message";
import { addDept, deleteDept, getDeptList, updateDept } from "@/api/system";
import { usePublicHooks } from "../../hooks";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h } from "vue";
import type { FormItemProps } from "../utils/types";
import { cloneDeep, isAllEmpty, deviceDetection } from "@pureadmin/utils";

export function useDept() {
  const form = reactive({
    name: "",
    status: null
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const { tagStyle } = usePublicHooks();

  const columns: TableColumnList = [
    { label: transformI18n("system.deptName"), prop: "name", width: 180, align: "left" },
    { label: transformI18n("system.sort"), prop: "sort", minWidth: 70 },
    {
      label: transformI18n("system.status"), prop: "status", minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.status)}>
          {row.status === 1 ? transformI18n("system.enabled") : transformI18n("system.disabled")}
        </el-tag>
      )
    },
    { label: transformI18n("system.createTime"), minWidth: 200, prop: "createTime",
      formatter: ({ createTime }) => dayjs(createTime).format("YYYY-MM-DD HH:mm:ss") },
    { label: transformI18n("system.remark"), prop: "remark", minWidth: 320 },
    { label: transformI18n("system.operation"), fixed: "right", width: 210, slot: "operation" }
  ];

  function handleSelectionChange(val) {
    console.log("handleSelectionChange", val);
  }

  function resetForm(formEl) {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  }

  async function onSearch() {
    loading.value = true;
    const { data } = await getDeptList(); // 这里是返回一维数组结构，前端自行处理成树结构，返回格式要求：唯一id加父节点parentId，parentId取父节点id
    let newData = data;
    if (!isAllEmpty(form.name)) {
      // 前端搜索部门名称
      newData = newData.filter(item => item.name.includes(form.name));
    }
    if (!isAllEmpty(form.status)) {
      // 前端搜索状态
      newData = newData.filter(item => item.status === form.status);
    }
    dataList.value = handleTree(newData); // 处理成树结构
    setTimeout(() => {
      loading.value = false;
    }, 500);
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

  function openDialog(title = transformI18n("system.add"), row?: FormItemProps) {
    addDialog({
      title: `${title} — ${transformI18n("menus.pureDept")}`,
      props: {
        formInline: {
          id: row?.id ?? null,
          higherDeptOptions: formatHigherDeptOptions(cloneDeep(dataList.value)),
          parentId: row?.parentId ?? null,
          name: row?.name ?? "",
          principal: row?.principal ?? "",
          phone: row?.phone ?? "",
          email: row?.email ?? "",
          sort: row?.sort ?? 0,
          status: row?.status ?? 1,
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
          message(`${title}${transformI18n("system.success")}: ${curData.name}`, { type: "success" });
          done(); onSearch();
        }
        FormRef.validate(valid => {
          if (valid) {
            if (title === transformI18n("system.add")) {
              delete curData.id;
              addDept(curData).then(res => {
                if (res.success) {
                  chores();
                } else {
                  message(res.msg, { type: "warning" });
                }
              });
            } else {
              updateDept(curData).then(res => {
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
    deleteDept([row.id]).then(res => {
      if (res.success) {
        message(`${transformI18n("system.deleteSuccess")}: ${row.name}`, { type: "success" });
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
    /** 搜索 */
    onSearch,
    /** 重置 */
    resetForm,
    /** 新增、修改部门 */
    openDialog,
    /** 删除部门 */
    handleDelete,
    handleSelectionChange
  };
}
