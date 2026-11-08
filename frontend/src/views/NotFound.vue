<template>
  <div class="page">
    <el-card shadow="never" class="page-card">
      <el-empty description="页面不存在或已被移动">
        <el-button type="primary" @click="router.push('/templates')">返回凭证模板</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
