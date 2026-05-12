import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { addMenu, deleteMenu, getMenuList, updateMenu } from "@/api/system";
import { $t, transformI18n } from "@/plugins/i18n";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h } from "vue";
import type { FormItemProps } from "../utils/types";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { cloneDeep, isAllEmpty, deviceDetection } from "@pureadmin/utils";

export function useMenu() {
  const form = reactive({
    title: ""
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);

  const getMenuType = (type, text = false) => {
    switch (type) {
      case 0:
        return text ? transformI18n("system.menuPage") : "primary";
      case 1:
        return text ? transformI18n("system.menuIframe") : "warning";
      case 2:
        return text ? transformI18n("system.menuLink") : "danger";
      case 3:
        return text ? transformI18n("system.menuButton") : "info";
    }
  };

  const columns: TableColumnList = [
    {
      label: transformI18n("system.menuName"),
      prop: "title",
      align: "left",
      cellRenderer: ({ row }) => (
        <>
          <span class="inline-block mr-1">
            {h(useRenderIcon(row.icon), { style: { paddingTop: "1px" } })}
          </span>
          <span>{transformI18n(row.title)}</span>
        </>
      )
    },
    {
      label: transformI18n("system.menuType"),
      prop: "menuType",
      width: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={getMenuType(row.menuType)}
          effect="plain"
        >
          {getMenuType(row.menuType, true)}
        </el-tag>
      )
    },
    { label: transformI18n("system.routePath"), prop: "path" },
    {
      label: transformI18n("system.component"),
      prop: "component",
      formatter: ({ path, component }) =>
        isAllEmpty(component) ? path : component
    },
    { label: transformI18n("system.auths"), prop: "auths" },
    { label: transformI18n("system.sort"), prop: "rank", width: 100 },
    {
      label: transformI18n("system.showLink"),
      prop: "showLink",
      formatter: ({ showLink }) =>
        showLink ? transformI18n("system.hide") : transformI18n("system.show"),
      width: 100
    },
    {
      label: transformI18n("system.operation"),
      fixed: "right",
      width: 210,
      slot: "operation"
    }
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
    const { data } = await getMenuList(); // 这里是返回一维数组结构，前端自行处理成树结构，返回格式要求：唯一id加父节点parentId，parentId取父节点id
    let newData = data;
    if (!isAllEmpty(form.title)) {
      // 前端搜索菜单名称
      newData = newData.filter(item =>
        transformI18n(item.title).includes(form.title)
      );
    }
    dataList.value = handleTree(newData); // 处理成树结构
    setTimeout(() => {
      loading.value = false;
    }, 500);
  }

  function formatHigherMenuOptions(treeList) {
    if (!treeList || !treeList.length) return;
    const newTreeList = [];
    for (let i = 0; i < treeList.length; i++) {
      treeList[i].title = transformI18n(treeList[i].title);
      formatHigherMenuOptions(treeList[i].children);
      newTreeList.push(treeList[i]);
    }
    return newTreeList;
  }

  function openDialog(
    title = transformI18n("system.add"),
    row?: FormItemProps
  ) {
    const isAdd = title === transformI18n("system.add");
    addDialog({
      title: `${title} — ${transformI18n("menus.pureSystemMenu")}`,
      props: {
        formInline: {
          id: row.id,
          menuType: row?.menuType ?? 0,
          higherMenuOptions: formatHigherMenuOptions(cloneDeep(dataList.value)),
          parentId: row?.parentId ?? null,
          title: row?.title ?? "",
          name: row?.name ?? "",
          path: row?.path ?? "",
          component: row?.component ?? "",
          rank: row?.rank ?? 99,
          redirect: row?.redirect ?? "",
          icon: row?.icon ?? "",
          extraIcon: row?.extraIcon ?? "",
          transitionName: "",
          enterTransition: row?.enterTransition ?? "",
          leaveTransition: row?.leaveTransition ?? "",
          activePath: row?.activePath ?? "",
          auths: row?.auths ?? "",
          frameSrc: row?.frameSrc ?? "",
          frameLoading: row?.frameLoading ?? true,
          keepAlive: row?.keepAlive ?? false,
          hiddenTag: row?.hiddenTag ?? false,
          fixedTag: row?.fixedTag ?? false,
          showLink: row?.showLink ?? true,
          showParent: row?.showParent ?? false
        }
      },
      width: "45%",
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
            `${title}${transformI18n("system.success")}: ${transformI18n(curData.title)}`,
            { type: "success" }
          );
          done();
          onSearch();
        }
        FormRef.validate(valid => {
          if (valid) {
            if (isAdd) {
              // 实际开发先调用新增接口，再进行下面操作
              addMenu(curData).then(res => {
                if (res.success) {
                  chores();
                }
              });
            } else {
              // 实际开发先调用修改接口，再进行下面操作
              updateMenu(curData).then(res => {
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

  function handleDelete(row) {
    deleteMenu([row.id]).then(res => {
      if (res.success) {
        message(
          `${transformI18n("system.deleteSuccess")}: ${transformI18n(row.title)}`,
          { type: "success" }
        );
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
    /** 新增、修改菜单 */
    openDialog,
    /** 删除菜单 */
    handleDelete,
    handleSelectionChange
  };
}
