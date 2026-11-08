<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>会计科目</h1>
        <p class="page-desc">科目用于凭证模板的分录选择；辅助项由模板自行配置，不在此维护。</p>
      </div>
      <el-button type="primary" @click="openCreate">新增科目</el-button>
    </div>

    <el-card shadow="never" class="page-card">
      <div class="filter-bar" role="search" aria-label="科目筛选">
        <el-input
          v-model="store.filters.keyword"
          class="filter-keyword"
          placeholder="搜索编码 / 名称 / 全称"
          clearable
          aria-label="关键词搜索"
          @input="onKeywordInput"
          @clear="applyFilters"
          @keyup.enter="applyFilters"
        />
        <el-select
          v-model="store.filters.status"
          class="filter-status"
          placeholder="全部状态"
          clearable
          aria-label="状态筛选"
          @change="applyFilters"
        >
          <el-option label="启用" value="enabled" />
          <el-option label="停用" value="disabled" />
        </el-select>
        <el-button @click="resetFilters">重置</el-button>
        <span class="filter-summary">共 {{ store.total }} 条</span>
      </div>

      <el-skeleton v-if="showSkeleton" :rows="5" animated />

      <template v-else>
        <el-table
          v-loading="store.loading"
          :data="store.list"
          row-key="id"
          aria-label="会计科目列表"
        >
          <el-table-column label="科目编码" prop="code" width="160">
            <template #default="{ row }">
              <span class="mono">{{ row.code }}</span>
            </template>
          </el-table-column>
          <el-table-column label="科目名称" prop="name" min-width="190" />
          <el-table-column label="科目全称" min-width="240">
            <template #default="{ row }">
              <span :class="{ 'cell-muted': !row.full_name }">{{ row.full_name || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" effect="plain" size="small">
                {{ row.status === 'enabled' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button link type="primary" :aria-label="`编辑科目 ${row.name}`" @click="openEdit(row)">
                  编辑
                </el-button>
                <el-button
                  link
                  :type="row.status === 'enabled' ? 'warning' : 'success'"
                  :aria-label="`${row.status === 'enabled' ? '停用' : '启用'}科目 ${row.name}`"
                  @click="toggleStatus(row)"
                >
                  {{ row.status === 'enabled' ? '停用' : '启用' }}
                </el-button>
                <el-button link type="danger" :aria-label="`删除科目 ${row.name}`" @click="removeAccount(row)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :image-size="80" description="暂无符合条件的科目，试试调整筛选条件" />
          </template>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :total="store.total"
            :current-page="store.filters.page"
            :page-size="store.filters.page_size"
            :page-sizes="[20, 50, 100]"
            @current-change="onPageChange"
            @size-change="onSizeChange"
          />
        </div>
      </template>
    </el-card>

    <AccountEditorDialog v-model="dialogVisible" :account="editingAccount" @saved="onSaved" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AccountEditorDialog from '../../components/AccountEditorDialog.vue'
import { HttpError, errorText } from '../../api/http'
import { useAccountStore } from '../../stores/account'
import type { AccountSummary } from '../../types'

const store = useAccountStore()
const dialogVisible = ref(false)
const editingAccount = ref<AccountSummary | null>(null)
let keywordTimer: ReturnType<typeof setTimeout> | undefined

const showSkeleton = computed(() => store.loading && !store.initialized)

onMounted(() => store.fetchList())
onUnmounted(() => clearTimeout(keywordTimer))

function onKeywordInput() {
  clearTimeout(keywordTimer)
  keywordTimer = setTimeout(applyFilters, 300)
}

function applyFilters() {
  clearTimeout(keywordTimer)
  store.filters.page = 1
  store.fetchList()
}

function resetFilters() {
  store.filters.keyword = ''
  store.filters.status = ''
  applyFilters()
}

function onPageChange(page: number) {
  store.filters.page = page
  store.fetchList()
}

function onSizeChange(size: number) {
  store.filters.page_size = size
  store.filters.page = 1
  store.fetchList()
}

function openCreate() {
  editingAccount.value = null
  dialogVisible.value = true
}

function openEdit(account: AccountSummary) {
  editingAccount.value = account
  dialogVisible.value = true
}

async function onSaved(created: boolean) {
  if (created) store.filters.page = 1
  await store.fetchList()
}

async function toggleStatus(account: AccountSummary) {
  try {
    const updated = await store.setStatus(account.id, account.status === 'disabled')
    ElMessage.success(updated.status === 'enabled' ? '科目已启用' : '科目已停用')
  } catch (error) {
    ElMessage.error(errorText(error, '状态更新失败，请稍后重试'))
  }
}

async function removeAccount(account: AccountSummary) {
  try {
    await ElMessageBox.confirm(`确定删除科目「${account.name}」吗？删除后不可恢复。`, '删除科目', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await store.remove(account.id)
    ElMessage.success('科目已删除')
    if (store.list.length === 1 && store.filters.page > 1) {
      store.filters.page -= 1
    }
    await store.fetchList()
  } catch (error) {
    if (error instanceof HttpError && error.code === 'ACCOUNT_IN_USE') {
      ElMessageBox.alert(
        '该科目已被凭证模板引用，无法删除。请改用「停用」：停用后不影响已保存的模板，只是不能再被新的分录选择。',
        '无法删除',
        { type: 'warning', confirmButtonText: '知道了' },
      )
      return
    }
    ElMessage.error(errorText(error, '删除失败，请稍后重试'))
  }
}
</script>

<style scoped>
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
}
</style>
