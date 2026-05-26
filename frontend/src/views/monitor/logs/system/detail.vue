<script setup lang="tsx">
import { ref } from "vue";
import { transformI18n } from "@/plugins/i18n";
import "vue-json-pretty/lib/styles.css";
import VueJsonPretty from "vue-json-pretty";

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
});

const columns = [
  {
    label: transformI18n("system.ip"),
    prop: "ip"
  },
  {
    label: transformI18n("system.location"),
    prop: "address"
  },
  {
    label: transformI18n("system.os"),
    prop: "system"
  },
  {
    label: transformI18n("system.browser"),
    prop: "browser"
  },
  {
    label: transformI18n("system.module"),
    prop: "module"
  },
  {
    label: transformI18n("system.requestTime"),
    prop: "requestTime"
  },
  {
    label: transformI18n("system.requestMethod"),
    prop: "method"
  },
  {
    label: transformI18n("system.requestDuration"),
    prop: "takesTime"
  },
  {
    label: transformI18n("system.requestUrl"),
    prop: "url",
    copy: true
  },
  {
    label: "TraceId",
    prop: "traceId",
    copy: true
  }
];

const dataList = ref([
  {
    title: transformI18n("system.responseHeaders"),
    name: "responseHeaders",
    data: (props.data[0] as any).responseHeaders
  },
  {
    title: transformI18n("system.responseBody"),
    name: "responseBody",
    data: (props.data[0] as any).responseBody
  },
  {
    title: transformI18n("system.requestHeaders"),
    name: "requestHeaders",
    data: (props.data[0] as any).requestHeaders
  },
  {
    title: transformI18n("system.requestBody"),
    name: "requestBody",
    data: (props.data[0] as any).requestBody
  }
]);
</script>

<template>
  <div>
    <el-scrollbar>
      <PureDescriptions border :data="data" :columns="columns" :column="5" />
    </el-scrollbar>
    <el-tabs :modelValue="'responseBody'" type="border-card" class="mt-4">
      <el-tab-pane
        v-for="(item, index) in dataList"
        :key="index"
        :name="item.name"
        :label="item.title"
      >
        <el-scrollbar max-height="calc(100vh - 240px)">
          <vue-json-pretty v-model:data="item.data" />
        </el-scrollbar>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
