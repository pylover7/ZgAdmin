import axios from "axios";
import type { App } from "vue";

let config: object = {};
const { VITE_PUBLIC_PATH } = import.meta.env;

const setConfig = (cfg?: unknown) => {
  config = Object.assign(config, cfg);
};

const getConfig = (key?: string): PlatformConfigs => {
  if (typeof key === "string") {
    const arr = key.split(".");
    if (arr && arr.length) {
      let data = config;
      arr.forEach(v => {
        if (data && typeof data[v] !== "undefined") {
          data = data[v];
        } else {
          data = null;
        }
      });
      return data;
    }
  }
  return config;
};

/** 获取项目动态全局配置 */
export const getPlatformConfig = async (app: App): Promise<undefined> => {
  app.config.globalProperties.$config = getConfig();
  return axios({
    method: "get",
    url: `${VITE_PUBLIC_PATH}platform-config.json`
  })
    .then(async ({ data: config }) => {
      let $config = app.config.globalProperties.$config;
      // 自动注入系统配置
      if (app && $config && typeof config === "object") {
        $config = Object.assign($config, config);
      }

      // 从后端 API 获取站点内容配置，覆盖静态值
      try {
        const { data: apiData } = await axios({
          method: "get",
          url: "/api/v1/base/init"
        });
        if (apiData?.success && apiData.data) {
          const siteInfo = apiData.data.site;
          $config.Title = siteInfo.site_name ?? $config.Title;
          $config.Locale = siteInfo.default_lang ?? $config.Locale;
          $config.SiteDesc = siteInfo.site_desc ?? $config.SiteDesc;
          $config.Logo = siteInfo.logo ?? $config.Logo;
          $config.Copyright = siteInfo.copyright ?? $config.Copyright;
          $config.Icp = siteInfo.icp ?? $config.Icp;
        }
      } catch {
        // API 不可用时静默降级，使用 platform-config.json 的值
        console.warn("[Config] 无法获取站点信息，使用默认配置");
      }

      app.config.globalProperties.$config = $config;
      setConfig($config);
      return $config;
    })
    .catch(() => {
      throw "请在public文件夹下添加platform-config.json配置文件";
    });
};

/** 本地响应式存储的命名空间 */
const responsiveStorageNameSpace = () => getConfig().ResponsiveStorageNameSpace;

const paginationConf = {
  total: 0,
  pageSize: 15,
  currentPage: 1,
  pageSizes: [5, 15, 30, 50, 100],
  background: true
};

export { getConfig, setConfig, responsiveStorageNameSpace, paginationConf };
