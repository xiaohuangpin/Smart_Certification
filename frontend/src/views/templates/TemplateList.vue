<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>凭证模板</h1>
        <p class="page-desc">模板以「场景化模板」为粒度维护；智能制证需先完成会计科目与模板配置。</p>
      </div>
      <el-button type="primary" @click="router.push('/templates/new')">新建模板</el-button>
    </div>

    <el-card shadow="never" class="page-card">
      <div class="filter-bar" role="search" aria-label="模板筛选">
        <el-input
          v-model="store.filters.keyword"
          class="filter-keyword"
          placeholder="搜索编码 / 名称 / 场景名称"
          clearable
          aria-label="关键词搜索"
          @input="onKeywordInput"
          @clear="applyFilters"
          @keyup.enter="applyFilters"
        />
        <el-input
          v-model="store.filters.tag"
          class="filter-tag"
          placeholder="按标签筛选"
          clearable
          aria-label="标签筛选"
          @change="applyFilters"
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
          aria-label="凭证模板列表"
        >
          <el-table-column label="模板编码" prop="code" width="170">
            <template #default="{ row }">
              <span class="mono">{{ row.code }}</span>
            </template>
          </el-table-column>
          <el-table-column label="模板名称" prop="name" min-width="180" />
          <el-table-column label="场景编码" prop="scenario_code" width="165">
            <template #default="{ row }">
              <span class="mono">{{ row.scenario_code }}</span>
            </template>
          </el-table-column>
          <el-table-column label="场景名称" prop="scenario_name" min-width="140" />
          <el-table-column label="标签" min-width="170">
            <template #default="{ row }">
              <div v-if="row.tags.length" class="tag-list">
                <el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain" type="info">{{ tag }}</el-tag>
              </div>
              <span v-else class="cell-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column label="版本" width="80" align="center">
            <template #default="{ row }">V{{ row.version }}</template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" effect="plain" size="small">
                {{ row.status === 'enabled' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button
                  link
                  type="primary"
                  :aria-label="`编辑模板 ${row.name}`"
                  @click="router.push(`/templates/${row.id}/edit`)"
                >
                  编辑
                </el-button>
                <el-button
                  v-if="row.status === 'enabled'"
                  link
                  type="warning"
                  :aria-label="`停用模板 ${row.name}`"
                  @click="disableTemplate(row)"
                >
                  停用
                </el-button>
                <el-button link type="danger" :aria-label="`删除模板 ${row.name}`" @click="removeTemplate(row)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :image-size="80" description="暂无符合条件的模板，试试调整筛选条件或新建模板" />
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { HttpError, errorText } from '../../api/http'
import { useTemplateStore } from '../../stores/template'
import type { TemplateSummary } from '../../types'

const router = useRouter()
const store = useTemplateStore()
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
  store.filters.tag = ''
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

async function disableTemplate(template: TemplateSummary) {
  try {
    await store.disable(template.id)
    ElMessage.success(`模板「${template.name}」已停用`)
    await store.fetchList()
  } catch (error) {
    ElMessage.error(errorText(error, '停用失败，请稍后重试'))
  }
}

async function removeTemplate(template: TemplateSummary) {
  try {
    await ElMessageBox.confirm(
      `确定删除模板「${template.name}」吗？删除后不可恢复，已保存的历史制证结果不受影响。`,
      '删除模板',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await store.remove(template.id)
    ElMessage.success('模板已删除')
    if (store.list.length === 1 && store.filters.page > 1) {
      store.filters.page -= 1
    }
    await store.fetchList()
  } catch (error) {
    if (error instanceof HttpError && error.code === 'TEMPLATE_IN_USE') {
      ElMessageBox.alert(
        '该模板已有制证记录，无法删除。请改用「停用」：停用后不能再被智能制证选用，历史制证结果不受影响。',
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

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
