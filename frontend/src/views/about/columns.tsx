import { getSystemVersion } from "@/api/system";
import { onMounted, ref } from "vue";

export function useColumns() {
  const { pkg, lastBuildTime, projectVersion } = __APP_INFO__;
  const { version, engines } = pkg;

  interface VersionInfo {
    version: string;
    project_name: string;
    description: string;
    environment: string;
    python_version: string;
    uv_version: string;
    release_time: string;
  }

  const versionInfo = ref<VersionInfo>({
    version: "",
    project_name: "",
    description: "",
    environment: "",
    python_version: "",
    uv_version: "",
    release_time: ""
  });

  const appColums = [
    {
      label: "当前版本",
      minWidth: 100,
      cellRenderer: () => {
        return (
          <el-tag size="large" class="text-base!">
            {projectVersion}
          </el-tag>
        );
      }
    },
    {
      label: "Python 版本",
      minWidth: 120,
      cellRenderer: () => (
        <el-tag size="large" class="text-base!">
          {versionInfo.value.python_version || "-"}
        </el-tag>
      )
    },
    {
      label: "uv 版本",
      minWidth: 120,
      cellRenderer: () => (
        <el-tag size="large" class="text-base!">
          {versionInfo.value.uv_version || "-"}
        </el-tag>
      )
    },
    {
      label: "代码仓库",
      minWidth: 140,
      cellRenderer: () => {
        return (
          <a href="https://cnb.cool/pylover/Tools/ZgAdmin" target="_blank">
            <span style="color: var(--el-color-primary)">ZgAdmin</span>
          </a>
        );
      }
    },
    {
      label: "报告问题",
      minWidth: 140,
      cellRenderer: () => {
        return (
          <a
            href="https://cnb.cool/pylover/Tools/ZgAdmin/-/issues"
            target="_blank"
          >
            <span style="color: var(--el-color-primary)">Issue</span>
          </a>
        );
      }
    }
  ];

  const columns = [
    {
      label: "当前版本",
      minWidth: 100,
      cellRenderer: () => {
        return (
          <el-tag size="large" class="text-base!">
            {version}
          </el-tag>
        );
      }
    },
    {
      label: "最后编译时间",
      minWidth: 120,
      cellRenderer: () => {
        return (
          <el-tag size="large" class="text-base!">
            {lastBuildTime}
          </el-tag>
        );
      }
    },
    {
      label: "推荐 node 版本",
      minWidth: 140,
      cellRenderer: () => {
        return (
          <el-tag size="large" class="text-base!">
            {engines.node}
          </el-tag>
        );
      }
    },
    {
      label: "推荐 bun 版本",
      minWidth: 140,
      cellRenderer: () => {
        return (
          <el-tag size="large" class="text-base!">
            {engines.bun}
          </el-tag>
        );
      }
    },
    {
      label: "完整版代码地址",
      minWidth: 140,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a
            href="https://github.com/pure-admin/vue-pure-admin"
            target="_blank"
          >
            <span style="color: var(--el-color-primary)">完整版代码链接</span>
          </a>
        );
      }
    },
    {
      label: "精简版代码地址",
      minWidth: 140,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a
            href="https://github.com/pure-admin/pure-admin-thin"
            target="_blank"
          >
            <span style="color: var(--el-color-primary)">精简版代码链接</span>
          </a>
        );
      }
    },
    {
      label: "文档地址",
      minWidth: 100,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a href="https://pure-admin.cn/" target="_blank">
            <span style="color: var(--el-color-primary)">文档链接</span>
          </a>
        );
      }
    },
    {
      label: "预览地址",
      minWidth: 100,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a href="https://pure-admin.github.io/vue-pure-admin" target="_blank">
            <span style="color: var(--el-color-primary)">预览链接</span>
          </a>
        );
      }
    }
  ];

  onMounted(async () => {
    try {
      getSystemVersion().then(res => {
        if (res.data) {
          versionInfo.value = res.data as unknown as VersionInfo;
        }
      });
    } catch {
      // 静默失败，页面显示占位符 "-"
    }
  });

  return {
    columns,
    appColums
  };
}
