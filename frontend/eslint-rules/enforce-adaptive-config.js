/**
 * ESLint 自定义规则：禁止在 views 目录下硬编码 adaptiveConfig。
 *
 * 使用 <pure-table adaptive> 时，必须通过 inject("adaptiveConfig") 获取配置，
 * 不允许直接写 :adaptiveConfig="{ offsetBottom: xxx }" 对象字面量。
 *
 * 正确用法：
 *   const adaptiveConfig = inject("adaptiveConfig");
 *   <pure-table adaptive :adaptiveConfig="adaptiveConfig" />
 *
 * 错误用法：
 *   <pure-table adaptive :adaptiveConfig="{ offsetBottom: 108 }" />
 */
export default {
  meta: {
    type: "problem",
    docs: {
      description:
        "禁止在 views 目录下硬编码 adaptiveConfig，必须使用 inject 获取",
      category: "Best Practices"
    },
    messages: {
      noLiteralAdaptiveConfig:
        "不允许硬编码 adaptiveConfig 对象字面量。请使用 inject('adaptiveConfig') 获取配置，参考：const adaptiveConfig = inject('adaptiveConfig')",
      missingAdaptiveConfig:
        '使用了 adaptive 属性但未绑定 :adaptiveConfig。请添加 :adaptiveConfig="adaptiveConfig"'
    },
    schema: []
  },
  create(context) {
    return {
      /** 处理 <pure-table adaptive :adaptiveConfig="{ ... }" /> */
      VStartTag(node) {
        const attrs = node.attributes;
        const hasAdaptive = attrs.some(
          attr =>
            attr.type === "VAttribute" &&
            !attr.directive &&
            attr.key.name === "adaptive"
        );
        if (!hasAdaptive) return;

        const adaptiveConfigAttr = attrs.find(
          attr =>
            attr.type === "VAttribute" &&
            attr.directive &&
            attr.key.name === "bind" &&
            attr.key.argument?.rawName === "adaptiveConfig"
        );

        if (!adaptiveConfigAttr) {
          context.report({
            node,
            messageId: "missingAdaptiveConfig"
          });
          return;
        }

        // :adaptiveConfig="..." 的值是 VExpressionContainer
        const expr = adaptiveConfigAttr.value;
        if (
          expr?.type === "VExpressionContainer" &&
          expr.expression?.type === "ObjectExpression"
        ) {
          context.report({
            node: adaptiveConfigAttr,
            messageId: "noLiteralAdaptiveConfig"
          });
        }
      }
    };
  }
};
