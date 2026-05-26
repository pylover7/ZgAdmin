<script setup lang="ts">
import { PropType } from "vue";
import { ListItem } from "../data";
import NoticeItem from "./NoticeItem.vue";
import { transformI18n } from "@/plugins/i18n";

const emit = defineEmits<{
  (e: "notice-click", noticeId: string): void;
}>();

defineProps({
  list: {
    type: Array as PropType<Array<ListItem>>,
    default: () => []
  },
  emptyText: {
    type: String,
    default: ""
  }
});
</script>

<template>
  <div v-if="list.length">
    <NoticeItem
      v-for="(item, index) in list"
      :key="index"
      :noticeItem="item"
      :isLast="index === list.length - 1"
      style="cursor: pointer"
      @click="emit('notice-click', item.noticeId)"
    />
  </div>
  <el-empty v-else :description="transformI18n(emptyText)" />
</template>
