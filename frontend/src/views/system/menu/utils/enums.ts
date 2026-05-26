import type { OptionsType } from "@/components/ReSegmented";
import { transformI18n } from "@/plugins/i18n";

const menuTypeOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.menuLabel"),
    value: 0
  },
  {
    label: "iframe",
    value: 1
  },
  {
    label: transformI18n("system.menu.externalLink"),
    value: 2
  },
  {
    label: transformI18n("system.menu.btnLabel"),
    value: 3
  }
];

const showLinkOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.showLabel"),
    tip: transformI18n("system.menu.showTip"),
    value: true
  },
  {
    label: transformI18n("system.menu.hideLabel"),
    tip: transformI18n("system.menu.hideTip"),
    value: false
  }
];

const fixedTagOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.fixed"),
    tip: transformI18n("system.menu.fixedTip"),
    value: true
  },
  {
    label: transformI18n("system.menu.unfixed"),
    tip: transformI18n("system.menu.unfixedTip"),
    value: false
  }
];

const keepAliveOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.cache"),
    tip: transformI18n("system.menu.cacheTip"),
    value: true
  },
  {
    label: transformI18n("system.menu.noCache"),
    tip: transformI18n("system.menu.noCacheTip"),
    value: false
  }
];

const hiddenTagOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.allow"),
    tip: transformI18n("system.menu.allowTip"),
    value: false
  },
  {
    label: transformI18n("system.menu.forbid"),
    tip: transformI18n("system.menu.forbidTip"),
    value: true
  }
];

const showParentOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.showParent"),
    tip: transformI18n("system.menu.showParentTip"),
    value: true
  },
  {
    label: transformI18n("system.menu.hideParent"),
    tip: transformI18n("system.menu.hideParentTip"),
    value: false
  }
];

const frameLoadingOptions: Array<OptionsType> = [
  {
    label: transformI18n("system.menu.loadingOn"),
    tip: transformI18n("system.menu.loadingOnTip"),
    value: true
  },
  {
    label: transformI18n("system.menu.loadingOff"),
    tip: transformI18n("system.menu.loadingOffTip"),
    value: false
  }
];

export {
  menuTypeOptions,
  showLinkOptions,
  fixedTagOptions,
  keepAliveOptions,
  hiddenTagOptions,
  showParentOptions,
  frameLoadingOptions
};
