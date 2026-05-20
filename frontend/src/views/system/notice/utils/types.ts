interface FormItemProps {
  /** 通知 ID */
  id: string;
  /** 通知标题 */
  title: string;
  /** 通知内容 */
  content: string;
  /** 通知类型：0-系统, 1-业务, 2-公告 */
  type: number;
  /** 通知级别：info/warning/important */
  level: string;
  /** 通知状态：0-草稿, 1-已发布 */
  status: number;
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
