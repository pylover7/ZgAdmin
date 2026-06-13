import { getSystemVersion, checkUpdate } from "@/api/system";
import { onMounted, ref } from "vue";
import { transformI18n } from "@/plugins/i18n";
import { ElMessage, ElNotification } from "element-plus";

export function useColumns() {
  const { pkg, lastBuildTime } = __APP_INFO__;
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

  const checking = ref(false);

  const handleCheckUpdate = async () => {
    checking.value = true;
    const res = await checkUpdate();
    checking.value = false;
    if (res.data?.has_update) {
      ElNotification({
        title: transformI18n("system.about.newVersionFound"),
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>${transformI18n("system.about.currentVersion")} ${res.data.current_version} → ${transformI18n("system.about.latestVersion")} ${res.data.latest_version}</p>
            ${res.data.release_url ? `<p style="margin-top: 8px;"><a href="${res.data.release_url}" target="_blank" style="color: var(--el-color-primary)">${transformI18n("system.about.viewChangelog")}</a></p>` : ""}
            <p style="margin-top: 8px; color: var(--el-text-color-secondary); font-size: 13px;">${transformI18n("system.about.updateCommand")}：<code>bash scripts/update.sh</code></p>
          </div>
        `,
        type: "warning",
        duration: 0
      });
    } else {
      ElMessage.success(transformI18n("system.about.alreadyLatest"));
    }
  };

  const appColums = [
    {
      label: transformI18n("system.about.currentVersion"),
      minWidth: 100,
      cellRenderer: () => {
        return (
          <el-tag size="large" class="text-base!">
            {versionInfo.value.version || "-"}
          </el-tag>
        );
      }
    },
    {
      label: transformI18n("system.about.pythonVersion"),
      minWidth: 120,
      cellRenderer: () => (
        <el-tag size="large" class="text-base!">
          {versionInfo.value.python_version || "-"}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.about.uvVersion"),
      minWidth: 120,
      cellRenderer: () => (
        <el-tag size="large" class="text-base!">
          {versionInfo.value.uv_version || "-"}
        </el-tag>
      )
    },
    {
      label: transformI18n("system.about.codeRepository"),
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
      label: transformI18n("system.about.reportIssue"),
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
      label: transformI18n("system.about.currentVersion"),
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
      label: transformI18n("system.about.lastBuildTime"),
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
      label: transformI18n("system.about.recommendedNodeVersion"),
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
      label: transformI18n("system.about.recommendedBunVersion"),
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
      label: transformI18n("system.about.fullVersionAddress"),
      minWidth: 140,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a
            href="https://github.com/pure-admin/vue-pure-admin"
            target="_blank"
          >
            <span style="color: var(--el-color-primary)">
              {transformI18n("system.about.fullVersionLink")}
            </span>
          </a>
        );
      }
    },
    {
      label: transformI18n("system.about.thinVersionAddress"),
      minWidth: 140,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a
            href="https://github.com/pure-admin/pure-admin-thin"
            target="_blank"
          >
            <span style="color: var(--el-color-primary)">
              {transformI18n("system.about.thinVersionLink")}
            </span>
          </a>
        );
      }
    },
    {
      label: transformI18n("system.about.docAddress"),
      minWidth: 100,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a href="https://pure-admin.cn/" target="_blank">
            <span style="color: var(--el-color-primary)">
              {transformI18n("system.about.docLink")}
            </span>
          </a>
        );
      }
    },
    {
      label: transformI18n("system.about.previewAddress"),
      minWidth: 100,
      className: "pure-version",
      cellRenderer: () => {
        return (
          <a href="https://pure-admin.github.io/vue-pure-admin" target="_blank">
            <span style="color: var(--el-color-primary)">
              {transformI18n("system.about.previewLink")}
            </span>
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
    appColums,
    checking,
    handleCheckUpdate
  };
}
