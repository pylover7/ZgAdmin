<script setup lang="ts">
import { deviceDetection } from "@pureadmin/utils";
import { useAccountManagement } from "../utils/useAccountManagement";

defineOptions({
  name: "AccountManagement"
});

const { list, onClick } = useAccountManagement();
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">{{ $t("system.accountManagement") }}</h3>
    <div v-for="(item, index) in list" :key="index">
      <div class="flex items-center">
        <div class="flex-1">
          <p>{{ item.title }}</p>
          <el-text class="mx-1" type="info">{{ item.illustrate }}</el-text>
        </div>
        <el-button
          :type="item.disabled ? 'info' : 'primary'"
          text
          :disabled="item.disabled"
          @click="onClick(item)"
        >
          {{ item.button }}
        </el-button>
      </div>
      <el-divider />
    </div>
  </div>
</template>

<style lang="scss" scoped></style>
