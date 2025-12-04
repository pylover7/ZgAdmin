// 完整版菜单比较多，将 rank 抽离出来，在此方便维护

const home = 0, // 平台规定只有 home 路由的 rank 才能为 0 ，所以后端在返回 rank 的时候需要从非 0 开始
  error = 110,
  system = 114,
  monitor = 115,
  about = 117;

export { home, error, system, monitor, about };
