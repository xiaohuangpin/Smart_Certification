<template>
  <el-dialog
    v-model="visible"
    :title="account ? '编辑科目' : '新增科目'"
    width="540px"
    :close-on-click-modal="false"
    @closed="submitting = false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="left"
      label-width="90px"
      @submit.prevent
    >
      <el-form-item label="科目编码" prop="code" :error="codeError">
        <div class="form-item-stack">
          <el-input
            v-model="form.code"
            :disabled="Boolean(account)"
            maxlength="20"
            placeholder="如 2221150000"
            aria-label="科目编码"
            @input="codeError = ''"
          />
          <div class="form-hint">{{ account ? '编码创建后不可修改' : '4–20 位字母、数字、下划线或短横线' }}</div>
        </div>
      </el-form-item>
      <el-form-item label="科目名称" prop="name">
        <el-input v-model="form.name" maxlength="50" placeholder="如 应交税费_应交房产税" aria-label="科目名称" />
      </el-form-item>
      <el-form-item label="科目全称" prop="full_name">
        <el-input v-model="form.full_name" maxlength="100" placeholder="可选，完整科目名称" aria-label="科目全称" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" aria-label="科目状态">
          <el-option label="启用" value="enabled" />
          <el-option label="停用" value="disabled" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button :disabled="submitting" @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { HttpError, errorText } from '../api/http'
import { useAccountStore } from '../stores/account'
import type { AccountCreateInput, AccountSummary } from '../types'

const props = defineProps<{ modelValue: boolean; account: AccountSummary | null }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean]; saved: [created: boolean] }>()

const store = useAccountStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const codeError = ref('')

const form = reactive<AccountCreateInput>({
  code: '',
  name: '',
  full_name: '',
  status: 'enabled',
})

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const rules: FormRules<AccountCreateInput> = {
  code: [
    { required: true, message: '请填写科目编码', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9_-]{4,20}$/,
      message: '科目编码需为 4–20 位字母、数字、下划线或短横线',
      trigger: 'blur',
    },
  ],
  name: [
    { required: true, message: '请填写科目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '科目名称需为 2–50 字', trigger: 'blur' },
  ],
  full_name: [{ max: 100, message: '科目全称最多 100 字', trigger: 'blur' }],
}

function syncForm() {
  codeError.value = ''
  const account = props.account
  Object.assign(form, {
    code: account?.code ?? '',
    name: account?.name ?? '',
    full_name: account?.full_name ?? '',
    status: account?.status ?? 'enabled',
  })
  nextTick(() => formRef.value?.clearValidate())
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) syncForm()
  },
)

async function submit() {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查表单中的必填项后再保存')
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: form.name.trim(),
      full_name: form.full_name.trim(),
      status: form.status,
    }
    if (props.account) {
      await store.update(props.account.id, payload)
      ElMessage.success('科目已更新')
    } else {
      await store.create({ ...payload, code: form.code.trim() })
      ElMessage.success('科目已新增')
    }
    emit('saved', !props.account)
    visible.value = false
  } catch (error) {
    if (error instanceof HttpError && error.code === 'ACCOUNT_CODE_DUPLICATED') {
      codeError.value = '科目编码已存在，请更换后重试'
      formRef.value?.scrollToField('code')
    } else {
      ElMessage.error(errorText(error, '保存失败，请稍后重试'))
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-item-stack {
  width: 100%;
}
</style>
