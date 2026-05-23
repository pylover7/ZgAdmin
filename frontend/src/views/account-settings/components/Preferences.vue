<script setup lang="ts">
import { deviceDetection } from "@pureadmin/utils";
import { usePreferences } from "../utils/usePreferences";
import { transformI18n } from "@/plugins/i18n";

defineOptions({
  name: "Preferences"
});

const { list, onChange } = usePreferences();
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">{{ transformI18n("system.preferences") }}</h3>
    <div v-for="(item, index) in list" :key="index">
      <div class="flex items-center">
        <div class="flex-1">
          <p>{{ item.title }}</p>
          <p class="wp-4">
            <el-text class="mx-1" type="info">
              {{ item.illustrate }}
            </el-text>
          </p>
        </div>
        <el-switch
          v-model="item.checked"
          inline-prompt
          :active-text="transformI18n('system.yes')"
          :inactive-text="transformI18n('system.no')"
          @change="(val: string | number | boolean) => onChange(!!val, item)"
        />
      </div>
      <el-divider />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.el-divider--horizontal {
  border-top: 0.1px var(--el-border-color) var(--el-border-style);
}
</style>
