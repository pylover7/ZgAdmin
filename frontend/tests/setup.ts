import { vi } from "vitest";
import { config } from "@vue/test-utils";

// ─── Mock js-cookie ───
vi.mock("js-cookie", () => ({
  default: {
    get: vi.fn(() => undefined),
    set: vi.fn(),
    remove: vi.fn()
  }
}));

// ─── Mock @pureadmin/utils (partial — only what's used in tests) ───
vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn()
  })),
  isString: vi.fn((v: unknown) => typeof v === "string"),
  isIncludeAllChildren: vi.fn(
    (children: string[], parent: string[]) =>
      children.every(c => parent.includes(c))
  ),
  isUrl: vi.fn((v: string) => v.startsWith("http")),
  isEqual: vi.fn((a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b)),
  isNumber: vi.fn((v: unknown) => typeof v === "number"),
  isBoolean: vi.fn((v: unknown) => typeof v === "boolean"),
  isFunction: vi.fn((v: unknown) => typeof v === "function"),
  debounce: vi.fn((fn: Function) => {
    let timer: ReturnType<typeof setTimeout>;
    return (...args: unknown[]) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), 0);
    };
  }),
  getKeyList: vi.fn((tree: any[], key: string) => {
    const result: unknown[] = [];
    const walk = (nodes: any[]) => {
      for (const n of nodes) {
        if (n[key] !== undefined) result.push(n[key]);
        if (n.children) walk(n.children);
      }
    };
    walk(tree);
    return result;
  }),
  cloneDeep: vi.fn((obj: unknown) => JSON.parse(JSON.stringify(obj))),
  isAllEmpty: vi.fn((v: unknown) => v === "" || v === null || v === undefined),
  intersection: vi.fn((a: string[], b: string[]) => a.filter(x => b.includes(x))),
  subBefore: vi.fn((str: string, char: string) => {
    const idx = str.indexOf(char);
    return idx === -1 ? str : str.substring(0, idx);
  }),
  getQueryMap: vi.fn(() => ({})),
  sum: vi.fn((arr: number[]) => arr.reduce((a, b) => a + b, 0)),
  formatBytes: vi.fn((bytes: number) => `${bytes} B`),
  deviceDetection: vi.fn(() => "pc")
}));

// ─── Mock responsive-storage ───
vi.mock("responsive-storage", () => ({
  default: {
    getData: vi.fn(() => null),
    install: vi.fn()
  }
}));

// ─── Mock element-plus ───
vi.mock("element-plus", () => ({
  ElMessage: Object.assign(
    vi.fn(() => ({ close: vi.fn() })),
    { closeAll: vi.fn() }
  )
}));

// ─── Mock vue-router ───
const mockPush = vi.fn();
const mockResetRouter = vi.fn();
vi.mock("@/router", () => ({
  router: {
    push: mockPush,
    addRoute: vi.fn(),
    hasRoute: vi.fn(() => false),
    getRoutes: vi.fn(() => []),
    currentRoute: { value: { meta: {}, path: "/", name: "" } },
    options: { routes: [{ path: "/", children: [] }] }
  },
  resetRouter: mockResetRouter,
  constantMenus: []
}));

// ─── Mock pinia store ───
vi.mock("@/store", () => ({
  store: {
    use: vi.fn()
  }
}));

// ─── Mock @/config ───
vi.mock("@/config", () => ({
  getConfig: vi.fn(() => ({})),
  setConfig: vi.fn(),
  responsiveStorageNameSpace: vi.fn(() => "responsive-"),
  paginationConf: {
    total: 0,
    pageSize: 15,
    currentPage: 1
  }
}));

// ─── Mock @/layout/types ───
vi.mock("@/layout/types", () => ({
  routerArrays: []
}));

// ─── Global Vue Test Utils config ───
config.global.stubs = {
  "router-link": true,
  "router-view": true
};

export { mockPush, mockResetRouter };
