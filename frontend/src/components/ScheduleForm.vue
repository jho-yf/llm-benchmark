<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('cancel')">
    <div class="bg-white rounded-lg shadow-xl w-[1100px] max-h-[90vh] overflow-y-auto p-6">
      <h2 class="text-lg font-semibold mb-4">{{ isEdit ? '编辑' : '新建' }}定时任务</h2>

      <!-- Basic: name + cron side by side -->
      <div class="grid grid-cols-2 gap-4 mb-5">
        <div>
          <label class="label">任务名称</label>
          <input v-model="form.name" class="input" placeholder="如：每周 MMLU 评测" />
        </div>
        <div>
          <label class="label">Cron 表达式</label>
          <div class="flex gap-2">
            <select @change="form.cron_expr = $event.target.value; $event.target.value = ''" class="cron-preset">
              <option value="">-- 预设 --</option>
              <option value="0 2 * * *">每天 2:00</option>
              <option value="0 2 * * 0">周日 2:00</option>
              <option value="0 2 * * 1">周一 2:00</option>
              <option value="0 2 1 * *">每月1号</option>
              <option value="0 */6 * * *">每6小时</option>
              <option value="0 */12 * * *">每12小时</option>
            </select>
            <input v-model="form.cron_expr" class="input flex-1" placeholder="0 2 * * 0" />
          </div>
        </div>
      </div>

      <!-- Two-column: LLM + Benchmark -->
      <div class="grid grid-cols-2 gap-5 mb-5">
        <!-- LLM Config -->
        <fieldset class="border rounded p-3">
          <legend class="text-sm font-semibold text-gray-600 px-2">模型配置</legend>
          <div class="space-y-2.5">
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">提供商</label>
                <select v-model="form.llm.provider" class="input">
                  <option value="openai">OpenAI</option>
                  <option value="azure">Azure</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="ollama">Ollama</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div>
                <label class="label">模型标识</label>
                <input v-model="form.llm.model_id" class="input" placeholder="gpt-4o" />
              </div>
            </div>
            <div>
              <label class="label">API 地址</label>
              <input v-model="form.llm.api_base" class="input" placeholder="https://api.openai.com/v1" />
            </div>
            <div>
              <label class="label">认证方式</label>
              <div class="flex gap-3 mt-0.5">
                <label class="flex items-center gap-1 text-xs">
                  <input type="radio" v-model="form.llm.auth_type" value="bearer" /> Bearer
                </label>
                <label class="flex items-center gap-1 text-xs">
                  <input type="radio" v-model="form.llm.auth_type" value="api_key" /> API Key
                </label>
                <label class="flex items-center gap-1 text-xs">
                  <input type="radio" v-model="form.llm.auth_type" value="none" /> 无
                </label>
              </div>
            </div>
            <div>
              <label class="label">密钥 / Token</label>
              <input v-model="form.llm.api_key" type="password" class="input" placeholder="sk-..." />
            </div>
            <div class="flex items-center gap-2">
              <button @click="handleTestConnection" class="px-3 py-1 text-sm border rounded hover:bg-gray-50" :disabled="testing">
                {{ testing ? '测试中...' : '测试连通性' }}
              </button>
              <span v-if="connResult" class="text-sm" :class="connResult.success ? 'text-green-600' : 'text-red-600'">
                {{ connResult.message }}
              </span>
            </div>
            <div>
              <label class="label">默认参数 (JSON, 可选)</label>
              <input v-model="llmParamsStr" class="input" placeholder='{"temperature": 0, "max_tokens": 2048}' />
            </div>
            <div>
              <label class="label">并发请求数</label>
              <input v-model.number="numConcurrent" type="number" min="1" max="64" class="input" />
              <p class="text-xs text-gray-400 mt-0.5">同时发送的 API 请求数，增大可加速评测（建议 4-16）</p>
            </div>
          </div>
        </fieldset>

        <!-- Benchmark Config -->
        <fieldset class="border rounded p-3">
          <legend class="text-sm font-semibold text-gray-600 px-2">Benchmark 配置</legend>
          <div class="space-y-2.5">
            <div>
              <label class="label">标准评测（选择后自动填充）</label>
              <select v-model="selectedPreset" @change="applyPreset" class="input">
                <option value="">-- 手动配置 --</option>
                <option v-for="p in presets" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
              <p v-if="selectedPresetDetail" class="mt-1 text-xs text-gray-500 bg-gray-50 rounded p-1.5 leading-relaxed">{{ selectedPresetDetail }}</p>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">名称</label>
                <input v-model="form.benchmark.name" class="input" />
              </div>
              <div>
                <label class="label">分类</label>
                <select v-model="form.benchmark.category" class="input">
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>
            <div>
              <label class="label">评测配置 (JSON)</label>
              <textarea v-model="benchConfigStr" class="input font-mono text-xs" rows="2"></textarea>
            </div>
            <div>
              <label class="label">运行参数 (JSON, 可选)</label>
              <textarea v-model="benchParamsStr" class="input font-mono text-xs" rows="2"></textarea>
            </div>
          </div>
        </fieldset>
      </div>

      <div class="flex justify-end gap-3">
        <button @click="$emit('cancel')" class="px-4 py-2 border rounded hover:bg-gray-50">取消</button>
        <button @click="handleSave" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { listPresets, listCategories, testConnection } from '../api'

const emit = defineEmits(['save', 'cancel'])
const props = defineProps({
  initial: { type: Object, default: null },
})

const isEdit = computed(() => !!props.initial)

const form = reactive({
  name: props.initial?.name ?? '',
  cron_expr: props.initial?.cron_expr ?? '0 2 * * 0',
  llm: {
    provider: props.initial?.llm_provider ?? 'openai',
    api_base: props.initial?.llm_api_base ?? '',
    api_key: props.initial?.llm_api_key ?? '',
    auth_type: props.initial?.llm_auth_type ?? 'bearer',
    model_id: props.initial?.llm_model_id ?? '',
    params: props.initial?.llm_params ?? null,
  },
  benchmark: {
    name: props.initial?.benchmark_name ?? '',
    category: props.initial?.benchmark_category ?? 'knowledge',
    config: props.initial?.benchmark_config ?? {},
    metrics: props.initial?.benchmark_metrics ?? null,
    params: props.initial?.benchmark_params ?? null,
  },
})

const llmParamsStr = computed({
  get: () => form.llm.params ? JSON.stringify(form.llm.params) : '',
  set: (v) => { try { form.llm.params = v ? JSON.parse(v) : null } catch {} },
})

const benchConfigStr = computed({
  get: () => JSON.stringify(form.benchmark.config, null, 2),
  set: (v) => { try { form.benchmark.config = JSON.parse(v) } catch {} },
})

const benchParamsStr = computed({
  get: () => form.benchmark.params ? JSON.stringify(form.benchmark.params, null, 2) : '',
  set: (v) => { try { form.benchmark.params = v ? JSON.parse(v) : null } catch {} },
})

const presets = ref([])
const categories = ref([])
const selectedPreset = ref('')
const testing = ref(false)
const connResult = ref(null)
const numConcurrent = ref(props.initial?.llm_params?.num_concurrent ?? 8)

const selectedPresetDetail = computed(() => {
  const p = presets.value.find(x => x.id === selectedPreset.value)
  return p?.detail || ''
})

onMounted(async () => {
  const [p, c] = await Promise.all([listPresets(), listCategories()])
  presets.value = p
  categories.value = c
})

function applyPreset() {
  const p = presets.value.find(x => x.id === selectedPreset.value)
  if (!p) return
  form.benchmark.name = p.name
  form.benchmark.category = p.category
  form.benchmark.config = p.config
  form.benchmark.metrics = p.metrics
}

async function handleTestConnection() {
  testing.value = true
  connResult.value = null
  try {
    const payload = {
      provider: form.llm.provider,
      api_base: form.llm.api_base,
      api_key: form.llm.api_key,
      auth_type: form.llm.auth_type,
      model_id: form.llm.model_id,
      params: form.llm.params,
    }
    if (props.initial?.id) payload.schedule_id = props.initial.id
    connResult.value = await testConnection(payload)
  } catch {
    connResult.value = { success: false, message: '请求失败' }
  } finally {
    testing.value = false
  }
}

function handleSave() {
  const llm = { ...form.llm }
  llm.params = { ...(llm.params || {}), num_concurrent: numConcurrent.value }
  const payload = {
    name: form.name,
    cron_expr: form.cron_expr,
    llm,
    benchmark: { ...form.benchmark },
  }
  emit('save', payload)
}
</script>

<style scoped>
.input {
  @apply w-full border border-gray-300 rounded px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500;
}
.label {
  @apply block text-xs font-medium text-gray-500 mb-1;
}
.cron-preset {
  @apply border border-gray-300 rounded px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 shrink-0;
  width: 10rem;
}
</style>
