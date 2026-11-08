<template>
  <el-config-provider :locale="zhCn">
    <div class="app-shell">
      <header class="app-header">
        <div class="brand">
          <div class="brand-mark" aria-hidden="true">智</div>
          <div>
            <div class="brand-title">智能制证</div>
            <div class="brand-sub">会计科目 · 凭证模板</div>
          </div>
        </div>
        <el-menu :default-active="activeMenu" mode="horizontal" :ellipsis="false" router class="app-nav">
          <el-menu-item index="/generation">智能制证</el-menu-item>
          <el-menu-item index="/templates">凭证模板</el-menu-item>
          <el-menu-item index="/accounts">会计科目</el-menu-item>
        </el-menu>
        <el-tag type="info" effect="plain" size="small">本地环境</el-tag>
      </header>
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const route = useRoute()
const activeMenu = computed(() => {
  if (route.path.startsWith('/generation')) return '/generation'
  return route.path.startsWith('/accounts') ? '/accounts' : '/templates'
})
</script>
