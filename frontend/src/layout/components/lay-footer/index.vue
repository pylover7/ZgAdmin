<script setup lang="ts">
import { getConfig } from "@/config";

const TITLE = getConfig("Title");
const COPYRIGHT = getConfig("Copyright");
const ICP = getConfig("Icp");
</script>

<template>
  <footer
    class="layout-footer text-[rgba(0,0,0,0.6)] dark:text-[rgba(220,220,242,0.8)]"
  >
    <span v-if="COPYRIGHT">{{ COPYRIGHT }}</span>
    <span v-else>
      Copyright © 2025-present
      <a
        class="hover:text-primary!"
        href="https://cnb.cool/pylover/Tools/ZgAdmin"
        target="_blank"
      >
        &nbsp;{{ TITLE }}
      </a>
    </span>
    <span v-if="ICP" class="ml-2">
      <a
        class="hover:text-primary!"
        href="https://beian.miit.gov.cn/"
        target="_blank"
      >
        {{ ICP }}
      </a>
    </span>
  </footer>
</template>

<style lang="scss" scoped>
.layout-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 0 0 8px;
  font-size: 14px;
}
</style>
