<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { transformI18n } from "@/plugins/i18n";
import { IconSelect } from "@/components/ReIcon";
import Segmented from "@/components/ReSegmented";
import ReAnimateSelector from "@/components/ReAnimateSelector";
import {
  menuTypeOptions,
  showLinkOptions,
  fixedTagOptions,
  keepAliveOptions,
  hiddenTagOptions,
  showParentOptions,
  frameLoadingOptions
} from "./utils/enums";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    id: 0,
    menuType: 0,
    higherMenuOptions: [],
    parentId: 0,
    title: "",
    name: "",
    path: "",
    component: "",
    rank: 99,
    redirect: "",
    icon: "",
    extraIcon: "",
    enterTransition: "",
    leaveTransition: "",
    activePath: "",
    auths: "",
    frameSrc: "",
    frameLoading: true,
    keepAlive: false,
    hiddenTag: false,
    fixedTag: false,
    showLink: true,
    showParent: false
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);

function getRef() {
  return ruleFormRef.value;
}

defineExpose({ getRef });
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="newFormInline"
    :rules="formRules"
    label-width="82px"
  >
    <el-row :gutter="30">
      <re-col>
        <el-form-item :label="$t('system.menuType')">
          <Segmented
            v-model="newFormInline.menuType"
            :options="menuTypeOptions"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item :label="$t('system.menu.parentMenu')">
          <el-cascader
            v-model="newFormInline.parentId"
            class="w-full"
            :options="newFormInline.higherMenuOptions"
            :props="{
              value: 'id',
              label: 'title',
              emitPath: false,
              checkStrictly: true
            }"
            clearable
            filterable
            :placeholder="$t('system.menu.selectParentMenu')"
          >
            <template #default="{ node, data }">
              <span>{{ transformI18n(data.title) }}</span>
              <span v-if="!node.isLeaf"> ({{ data.children.length }}) </span>
            </template>
          </el-cascader>
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menuName')" prop="title">
          <el-input
            v-model="newFormInline.title"
            clearable
            :placeholder="$t('system.menu.enterMenuName')"
          />
        </el-form-item>
      </re-col>
      <re-col v-if="newFormInline.menuType !== 3" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.routeName')" prop="name">
          <el-input
            v-model="newFormInline.name"
            clearable
            :placeholder="$t('system.menu.enterRouteName')"
          />
        </el-form-item>
      </re-col>

      <re-col v-if="newFormInline.menuType !== 3" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.routePath')" prop="path">
          <el-input
            v-model="newFormInline.path"
            clearable
            :placeholder="$t('system.menu.enterRoutePath')"
          />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.component')">
          <el-input
            v-model="newFormInline.component"
            clearable
            :placeholder="$t('system.menu.enterComponent')"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.menuSort')">
          <el-input-number
            v-model="newFormInline.rank"
            class="w-full!"
            :min="1"
            :max="9999"
            controls-position="right"
          />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.menu.redirect')">
          <el-input
            v-model="newFormInline.redirect"
            clearable
            :placeholder="$t('system.menu.enterRedirect')"
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType !== 3"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.menu.menuIcon')">
          <IconSelect v-model="newFormInline.icon" class="w-full" />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType !== 3"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.menu.extraIcon')">
          <el-input
            v-model="newFormInline.extraIcon"
            clearable
            :placeholder="$t('system.menu.extraIconPlaceholder')"
          />
        </el-form-item>
      </re-col>

      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.enterTransition')">
          <ReAnimateSelector
            v-model="newFormInline.enterTransition"
            :placeholder="$t('system.menu.selectEnterTransition')"
          />
        </el-form-item>
      </re-col>
      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.leaveTransition')">
          <ReAnimateSelector
            v-model="newFormInline.leaveTransition"
            :placeholder="$t('system.menu.selectLeaveTransition')"
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.menu.activeMenu')">
          <el-input
            v-model="newFormInline.activePath"
            clearable
            :placeholder="$t('system.menu.enterActiveMenu')"
          />
        </el-form-item>
      </re-col>
      <re-col v-if="newFormInline.menuType === 3" :value="12" :xs="24" :sm="24">
        <!-- 按钮级别权限设置 -->
        <el-form-item :label="$t('system.menu.authLabel')" prop="auths">
          <el-input
            v-model="newFormInline.auths"
            clearable
            :placeholder="$t('system.menu.enterAuth')"
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType === 1"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <!-- iframe -->
        <el-form-item :label="$t('system.menu.frameUrl')">
          <el-input
            v-model="newFormInline.frameSrc"
            clearable
            :placeholder="$t('system.menu.enterFrameUrl')"
          />
        </el-form-item>
      </re-col>
      <re-col v-if="newFormInline.menuType === 1" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.frameLoading')">
          <Segmented
            :modelValue="newFormInline.frameLoading ? 0 : 1"
            :options="frameLoadingOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.frameLoading = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType !== 3"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.menu.showLinkLabel')">
          :modelValue="newFormInline.showLink ? 0 : 1"
          :options="showLinkOptions" @change=" ({ option: { value } }) => {
          newFormInline.showLink = value; } " />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType !== 3"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item :label="$t('system.menu.showParentLabel')">
          <Segmented
            :modelValue="newFormInline.showParent ? 0 : 1"
            :options="showParentOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.showParent = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.keepAliveLabel')">
          <Segmented
            :modelValue="newFormInline.keepAlive ? 0 : 1"
            :options="keepAliveOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.keepAlive = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.hiddenTagLabel')">
          <Segmented
            :modelValue="newFormInline.hiddenTag ? 1 : 0"
            :options="hiddenTagOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.hiddenTag = value;
              }
            "
          />
        </el-form-item>
      </re-col>
      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item :label="$t('system.menu.fixedTagLabel')">
          <Segmented
            :modelValue="newFormInline.fixedTag ? 0 : 1"
            :options="fixedTagOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.fixedTag = value;
              }
            "
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
