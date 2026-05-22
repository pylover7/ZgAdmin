export type Result = {
  code: number;
  msg: string;
  success: boolean;
  data?: Array<any>;
};

export type RoleAuthResult = {
  code: number;
  msg: string;
  success: boolean;
  data?: {
    menus: string[];
    apis: string[];
  };
};

export type ResultTable = Result & {
  /** 总条目数 */
  total?: number;
  /** 每页显示条目个数 */
  pageSize?: number;
  /** 当前页数 */
  currentPage?: number;
};
