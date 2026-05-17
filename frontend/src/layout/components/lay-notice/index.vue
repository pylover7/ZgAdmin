<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import NoticeList from "./components/NoticeList.vue";
import { type TabItem, type UnreadResult, transformNotice } from "./data";
import { getUnreadNotices, markNoticeRead, markAllRead } from "@/api/notice";
import { message } from "@/utils/message";

import BellIcon from "~icons/lucide/bell";
import ArrowRightIcon from "~icons/ri/arrow-right-s-line";

const { t } = useI18n();
const router = useRouter();
const dropdownRef = ref();

// ─── 通知 Tab 数据 ───
const notices = ref<TabItem[]>([
  {
    key: "1",
    name: "status.pureNotify",
    list: [],
    emptyText: "status.pureNoNotify"
  }
]);

const activeKey = ref("1");
const unreadCount = ref(0);

// ─── 计算属性 ───
const getLabel = computed(
  () => (item: TabItem) =>
    t(item.name) + (item.list.length > 0 ? `(${item.list.length})` : "")
);

const currentNoticeHasData = computed(() => {
  const currentNotice = notices.value.find(
    item => item.key === activeKey.value
  );
  return currentNotice && currentNotice.list.length > 0;
});

const hasAnyNoticeData = computed(() => {
  return notices.value.some(
    item => Array.isArray(item.list) && item.list.length > 0
  );
});

// ─── 拉取未读通知 ───
async function fetchUnread() {
  try {
    const { data } = await getUnreadNotices();
    const result = data as unknown as UnreadResult;
    unreadCount.value = result.count;
    const notifyTab = notices.value.find(item => item.key === "1");
    if (notifyTab) {
      notifyTab.list = (result.list || []).map(transformNotice);
    }
  } catch {
    // 静默处理，避免影响用户体验
  }
}

// ─── 标记单条已读 ───
async function onNoticeClick(noticeId: string) {
  try {
    await markNoticeRead(noticeId);
    await fetchUnread(); // 刷新列表
  } catch {
    message("标记已读失败", { type: "error" });
  }
}

// ─── 全部标记已读 ───
async function onMarkAsRead() {
  try {
    await markAllRead();
    message("已全部标为已读", { type: "success" });
    await fetchUnread();
  } catch {
    message("操作失败", { type: "error" });
  }
}

// ─── 查看更多 → 跳转通知管理页 ───
function onWatchMore() {
  dropdownRef.value.handleClose();
  router.push("/system/notice");
}

// ─── 定时轮询 (30s) ───
let timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  fetchUnread();
  timer = setInterval(fetchUnread, 30_000);
});

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <el-dropdown ref="dropdownRef" trigger="click" placement="bottom-end">
    <span
      :class="['dropdown-badge', 'navbar-bg-hover', 'select-none', 'mr-1.75']"
    >
      <el-badge is-dot :hidden="!hasAnyNoticeData">
        <span class="header-notice-icon">
          <IconifyIconOffline :icon="BellIcon" />
        </span>
      </el-badge>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-tabs
          v-model="activeKey"
          :stretch="true"
          class="dropdown-tabs"
          :style="{ width: notices.length === 0 ? '200px' : '330px' }"
        >
          <el-empty
            v-if="notices.length === 0"
            :description="t('status.pureNoMessage')"
            :image-size="60"
          />
          <span v-else>
            <template v-for="item in notices" :key="item.key">
              <el-tab-pane :label="getLabel(item)" :name="`${item.key}`">
                <el-scrollbar max-height="345px">
                  <div class="noticeList-container">
                    <NoticeList
                      :list="item.list"
                      :emptyText="item.emptyText"
                      @notice-click="onNoticeClick"
                    />
                  </div>
                </el-scrollbar>
              </el-tab-pane>
            </template>
          </span>
        </el-tabs>
        <div
          v-if="currentNoticeHasData"
          class="border-t border-t-(--el-border-color-light) text-sm"
        >
          <div class="flex-bc m-1">
            <el-button type="primary" size="small" text @click="onWatchMore">
              {{ t("buttons.pureWatchMore") }}
              <IconifyIconOffline :icon="ArrowRightIcon" />
            </el-button>
            <el-button type="primary" size="small" text @click="onMarkAsRead">
              {{ t("buttons.pureMarkAsRead") }}
            </el-button>
          </div>
        </div>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style lang="scss" scoped>
/* 铃铛摇晃动画 — 保持不变 */
@keyframes pure-bell-ring {
  0%,
  100% {
    transform-origin: top;
  }
  15% {
    transform: rotateZ(10deg);
  }
  30% {
    transform: rotateZ(-10deg);
  }
  45% {
    transform: rotateZ(5deg);
  }
  60% {
    transform: rotateZ(-5deg);
  }
  75% {
    transform: rotateZ(2deg);
  }
}

.dropdown-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 48px;
  cursor: pointer;

  .header-notice-icon {
    font-size: 16px;
  }

  &:hover {
    .header-notice-icon svg {
      animation: pure-bell-ring 1s both;
    }
  }
}

.dropdown-tabs {
  .noticeList-container {
    padding: 15px 24px 0;
  }

  :deep(.el-tabs__header) {
    margin: 0;
  }
  :deep(.el-tabs__nav-wrap)::after {
    height: 1px;
  }
  :deep(.el-tabs__nav-wrap) {
    padding: 0 36px;
  }
}
</style>
