<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('cancel')">
    <div class="bg-white rounded-lg shadow-xl w-[1100px] max-h-[90vh] overflow-y-auto p-6">
      <h2 class="text-lg font-semibold mb-4">{{ readonly ? '查看' : (isEdit ? '编辑' : '新建') }}定时任务</h2>

      <!-- Basic: name + cron side by side -->
      <div class="grid grid-cols-2 gap-4 mb-5">
        <div>
          <label class="label">任务名称</label>
          <input v-model="form.name" :disabled="readonly" class="input" :class="hasError('任务名称') ? 'ring-1 ring-red-400' : ''" placeholder="如：每周 MMLU 评测" />
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="label">Cron 表达式</label>
            <div class="flex gap-2">
              <select @change="readonly ? null : (form.cron_expr = $event.target.value); $event.target.value = ''" :disabled="readonly" class="cron-preset">
                <option value="">-- 预设 --</option>
                <option value="0 2 * * *">每天 2:00</option>
                <option value="0 2 * * 0">周日 2:00</option>
                <option value="0 2 * * 1">周一 2:00</option>
                <option value="0 2 1 * *">每月1号</option>
                <option value="0 */6 * * *">每6小时</option>
                <option value="0 */12 * * *">每12小时</option>
              </select>
              <input v-model="form.cron_expr" :disabled="readonly" class="input flex-1" :class="hasError('Cron 表达式') ? 'ring-1 ring-red-400' : ''" placeholder="0 2 * * 0" />
            </div>
          </div>
          <div>
            <label class="label">到期停用时间 <span class="hint" data-hint="到达此时间后自动停用任务，不填则永不停用"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
            <input v-model="expiresAt" type="datetime-local" :disabled="readonly" class="input" />
          </div>
        </div>
      </div>

      <!-- Two-column: LLM + Benchmark -->
      <div class="grid grid-cols-2 gap-5 mb-5">
        <!-- LLM Config -->
        <fieldset class="border rounded p-3">
          <legend class="text-sm font-semibold text-gray-600 px-2">模型配置</legend>
          <div class="space-y-2.5">
            <div>
              <label class="label">模型标识</label>
              <input v-model="form.llm.model_id" :disabled="readonly" class="input" :class="hasError('模型标识') ? 'ring-1 ring-red-400' : ''" placeholder="gpt-4o" />
            </div>
            <div>
              <label class="label">API 地址</label>
              <input v-model="form.llm.api_base" :disabled="readonly" class="input" :class="hasError('API 地址') ? 'ring-1 ring-red-400' : ''" placeholder="https://api.openai.com/v1" />
            </div>
            <div>
              <label class="label">认证方式</label>
              <div class="flex gap-3 mt-0.5">
                <label class="flex items-center gap-1 text-xs">
                  <input type="radio" v-model="form.llm.auth_type" :disabled="readonly" value="bearer" /> Bearer
                </label>
                <label class="flex items-center gap-1 text-xs">
                  <input type="radio" v-model="form.llm.auth_type" :disabled="readonly" value="api_key" /> API Key
                </label>
                <label class="flex items-center gap-1 text-xs">
                  <input type="radio" v-model="form.llm.auth_type" :disabled="readonly" value="none" /> 无
                </label>
              </div>
            </div>
            <div>
              <label class="label">密钥 / Token</label>
              <input v-model="form.llm.api_key" type="password" :disabled="readonly" class="input" :class="hasError('密钥') ? 'ring-1 ring-red-400' : ''" placeholder="sk-..." />
            </div>
            <div v-if="!readonly" class="flex items-center gap-2">
              <button @click="handleTestConnection" class="px-3 py-1 text-sm border rounded hover:bg-gray-50" :disabled="testing">
                {{ testing ? '测试中...' : '测试连通性' }}
              </button>
              <span v-if="connResult" class="text-sm" :class="connResult.success ? 'text-green-600' : 'text-red-600'">
                {{ connResult.message }}
              </span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">Temperature <span class="hint" data-hint="控制生成随机性，0 为确定性输出，值越高越随机（范围 0-2）"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <input v-model.number="llmTemperature" type="number" min="0" max="2" step="0.1" :disabled="readonly" class="input" />
              </div>
              <div>
                <label class="label">最大输出 Tokens <span class="hint" data-hint="模型单次请求的最大输出 token 数"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <input v-model.number="llmMaxTokens" type="number" min="1" max="128000" :disabled="readonly" class="input" />
              </div>
            </div>
            <div class="flex items-center gap-6">
              <div class="flex-1">
                <label class="label">并发请求数 <span class="hint" data-hint="同时发送的 API 请求数，增大可加速评测（建议 4-16）"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <input v-model.number="numConcurrent" type="number" min="1" max="64" :disabled="readonly" class="input" />
              </div>
              <div>
                <label class="label">流式输出 <span class="hint" data-hint="开启后以 SSE 流式请求 API，AI 网关可正确统计 Token 用量"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <label class="flex items-center gap-1.5 mt-0.5 cursor-pointer select-none">
                  <input type="checkbox" v-model="form.llm.stream" :disabled="readonly" class="accent-blue-600 w-4 h-4" />
                  <span class="text-sm">Stream</span>
                </label>
              </div>
            </div>
          </div>
        </fieldset>

        <!-- Benchmark Config -->
        <fieldset class="border rounded p-3">
          <legend class="text-sm font-semibold text-gray-600 px-2 flex items-center gap-2">
            Benchmark 配置
            <button @click="openConfigEditor" class="text-gray-400 hover:text-blue-600" title="查看 JSON 配置">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
            </button>
          </legend>
          <div class="space-y-2.5">
            <div class="relative" ref="dropdownRef">
              <label class="label">标准评测（可多选，按顺序串行执行）</label>
              <div @click="!readonly && (showDropdown = !showDropdown)"
                class="min-h-[38px] border rounded px-2 py-1.5 flex flex-wrap gap-1 cursor-text text-sm"
                :class="readonly ? 'bg-gray-50' : (hasError('Benchmark 配置') ? 'ring-1 ring-red-400' : '')">
                <span v-if="!selectedPresets.length" class="text-gray-400">选择评测基准...</span>
                <template v-for="(id, idx) in selectedPresets" :key="id">
                  <span class="inline-flex items-center gap-0.5 bg-blue-50 text-blue-700 text-xs rounded pl-1.5 pr-0.5 py-0.5">
                    <span v-if="selectedPresets.length > 1" class="text-blue-400 mr-0.5 font-mono text-[10px]">{{ idx + 1 }}.</span>
                    {{ presetName(id) }}
                    <span v-if="!readonly" class="flex items-center">
                      <button v-if="idx > 0" @click.stop="movePreset(idx, -1)" class="px-0.5 text-blue-400 hover:text-blue-600" title="上移">▲</button>
                      <button v-if="idx < selectedPresets.length - 1" @click.stop="movePreset(idx, 1)" class="px-0.5 text-blue-400 hover:text-blue-600" title="下移">▼</button>
                      <button @click.stop="removePreset(idx)" class="px-0.5 text-blue-400 hover:text-red-500" title="移除">&times;</button>
                    </span>
                  </span>
                </template>
              </div>
              <div v-if="showDropdown && !readonly"
                class="absolute left-0 right-0 top-full mt-1 bg-white border rounded shadow-lg z-30 max-h-60 overflow-y-auto">
                <label v-for="p in presets" :key="p.id"
                  class="flex items-start gap-2 text-sm cursor-pointer hover:bg-gray-50 px-3 py-2 border-b last:border-0">
                  <input type="checkbox" :value="p.id" :checked="selectedPresets.includes(p.id)" @change="togglePreset(p.id)" class="accent-blue-600 mt-0.5" />
                  <div>
                    <span class="font-medium">{{ p.name }}</span>
                    <p class="text-xs text-gray-400">{{ p.description }}</p>
                  </div>
                </label>
              </div>
            </div>
            <div>
              <label class="label">名称</label>
              <input v-model="form.benchmark.name" :disabled="readonly" class="input" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">Few-shot 数量 <span class="hint" data-hint="给模型提供的示例数量，0 表示零样本"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <input v-model.number="numFewshot" type="number" min="0" max="64" :disabled="readonly" class="input" />
              </div>
              <div>
                <label class="label">最大生成 Tokens <span class="hint" data-hint="模型每次回答的最大 token 数"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <input v-model.number="maxTokens" type="number" min="1" max="65536" :disabled="readonly" class="input" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">样本数量限制 <span class="hint" data-hint="限制评测样本数量，不填则使用全部样本"><svg viewBox="0 0 16 16" fill="currentColor" class="w-3.5 h-3.5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11zM8 5a.75.75 0 100 1.5A.75.75 0 008 5zm-.75 3a.75.75 0 011.5 0v2.5a.75.75 0 01-1.5 0V8z"/></svg></span></label>
                <input v-model.number="sampleLimit" type="number" min="1" :disabled="readonly" class="input" placeholder="不填则使用全部样本" />
              </div>
              <div></div>
            </div>
          </div>
        </fieldset>
      </div>

      <div class="flex items-center justify-end gap-3">
        <div v-if="!readonly && validationErrors.length" class="text-xs text-red-500 mr-auto">
          请填写：{{ validationErrors.join('、') }}
        </div>
        <template v-if="readonly">
          <button @click="$emit('cancel')" class="px-4 py-2 border rounded hover:bg-gray-50">关闭</button>
        </template>
        <template v-else>
          <button @click="$emit('cancel')" class="px-4 py-2 border rounded hover:bg-gray-50">取消</button>
          <button @click="handleSave" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">保存</button>
        </template>
      </div>

      <!-- Config JSON Editor Modal -->
      <div v-if="showConfigEditor" class="fixed inset-0 bg-black/40 flex items-center justify-center z-[60]" @click.self="showConfigEditor = false">
        <div class="bg-white rounded-lg shadow-xl w-[700px] max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between px-4 py-3 border-b">
            <h3 class="text-sm font-semibold text-gray-700">评测配置 (JSON)</h3>
            <div class="flex items-center gap-2">
              <button v-if="!readonly" @click="formatConfigJson" class="px-2 py-1 text-xs border rounded hover:bg-gray-50">格式化</button>
              <button @click="showConfigEditor = false" class="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
            </div>
          </div>
          <textarea
            ref="configEditorRef"
            v-model="configEditorText"
            class="flex-1 min-h-[400px] font-mono text-sm p-4 resize-none focus:outline-none"
            :class="readonly ? 'bg-gray-50' : ''"
            :readonly="readonly"
            spellcheck="false"
          ></textarea>
          <div class="flex items-center justify-between px-4 py-3 border-t">
            <span v-if="configEditorError" class="text-xs text-red-500">{{ configEditorError }}</span>
            <span v-else class="text-xs text-green-500">JSON 有效</span>
            <div class="flex gap-2">
              <button @click="showConfigEditor = false" class="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">{{ readonly ? '关闭' : '取消' }}</button>
              <button v-if="!readonly" @click="applyConfigJson" class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">应用</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { listPresets, testConnection } from '../api'

const emit = defineEmits(['save', 'cancel'])
const props = defineProps({
  initial: { type: Object, default: null },
  readonly: { type: Boolean, default: false },
})

const isEdit = computed(() => !!props.initial)

const form = reactive({
  name: props.initial?.name ?? '',
  cron_expr: props.initial?.cron_expr ?? '0 2 * * 0',
  llm: {
    api_base: props.initial?.llm_api_base ?? '',
    api_key: props.initial?.llm_api_key ?? '',
    auth_type: props.initial?.llm_auth_type ?? 'bearer',
    model_id: props.initial?.llm_model_id ?? '',
    stream: props.initial?.llm_stream ?? true,
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

const llmTemperature = ref(props.initial?.llm_params?.temperature ?? 0)
const llmMaxTokens = ref(props.initial?.llm_params?.max_tokens ?? 2048)

const presets = ref([])
const selectedPresets = ref([])
const testing = ref(false)
const connResult = ref(null)
const numConcurrent = ref(props.initial?.llm_params?.num_concurrent ?? 4)
const validationErrors = ref([])
const showDropdown = ref(false)
const dropdownRef = ref(null)

function presetName(id) {
  return presets.value.find(p => p.id === id)?.name || id
}

function togglePreset(id) {
  const idx = selectedPresets.value.indexOf(id)
  if (idx >= 0) selectedPresets.value.splice(idx, 1)
  else selectedPresets.value.push(id)
}

function removePreset(idx) {
  selectedPresets.value.splice(idx, 1)
}

function movePreset(idx, dir) {
  const arr = selectedPresets.value
  const target = idx + dir
  if (target < 0 || target >= arr.length) return
  ;[arr[idx], arr[target]] = [arr[target], arr[idx]]
  // Trigger reactivity
  selectedPresets.value = [...arr]
}

function onClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

// Extract fewshot from initial config
const _initFewshot = props.initial?.benchmark_config?.num_fewshot
const _initFewshotVal = _initFewshot
  ? (typeof _initFewshot === 'object' ? Object.values(_initFewshot)[0] : _initFewshot)
  : 0

const numFewshot = ref(_initFewshotVal ?? 0)
const maxTokens = ref(props.initial?.benchmark_config?.generation_kwargs?.max_gen_toks ?? 512)
const sampleLimit = ref(props.initial?.benchmark_config?.limit ?? null)

function _toLocalDatetime(isoStr) {
  if (!isoStr) return ''
  // datetime-local input needs "YYYY-MM-DDTHH:mm" in local time
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const expiresAt = ref(_toLocalDatetime(props.initial?.expires_at ?? null))

function validate() {
  const errors = []
  if (!form.name.trim()) errors.push('任务名称')
  if (!form.cron_expr.trim()) errors.push('Cron 表达式')
  if (!form.llm.model_id.trim()) errors.push('模型标识')
  if (!form.llm.api_base.trim()) errors.push('API 地址')
  if (form.llm.auth_type !== 'none' && !form.llm.api_key?.trim()) errors.push('密钥')
  if (!form.benchmark.config?.tasks?.length) errors.push('Benchmark 配置')
  validationErrors.value = errors
  return errors.length === 0
}

function hasError(field) {
  return validationErrors.value.includes(field)
}

// Sync friendly fields → bench config
function syncConfigFromFields() {
  const config = form.benchmark.config
  const tasks = config.tasks || []
  const fewshotMap = {}
  for (const t of tasks) fewshotMap[t] = numFewshot.value
  config.num_fewshot = fewshotMap
  config.generation_kwargs = { ...(config.generation_kwargs || {}), max_gen_toks: maxTokens.value }
  config.limit = sampleLimit.value || null
}

watch([numFewshot, maxTokens, sampleLimit], () => syncConfigFromFields())

// Config JSON editor
const showConfigEditor = ref(false)
const configEditorText = ref('')
const configEditorError = ref('')
const configEditorRef = ref(null)

function openConfigEditor() {
  configEditorText.value = JSON.stringify(form.benchmark.config, null, 2)
  configEditorError.value = ''
  showConfigEditor.value = true
}

function formatConfigJson() {
  try {
    configEditorText.value = JSON.stringify(JSON.parse(configEditorText.value), null, 2)
    configEditorError.value = ''
  } catch (e) {
    configEditorError.value = '格式化失败: ' + e.message
  }
}

watch(configEditorText, (v) => {
  if (!v.trim()) { configEditorError.value = ''; return }
  try { JSON.parse(v); configEditorError.value = '' }
  catch (e) { configEditorError.value = e.message }
})

function applyConfigJson() {
  try {
    const parsed = JSON.parse(configEditorText.value)
    form.benchmark.config = parsed
    // Sync friendly fields back from parsed config
    if (parsed.num_fewshot) {
      const vals = typeof parsed.num_fewshot === 'object' ? Object.values(parsed.num_fewshot) : [parsed.num_fewshot]
      numFewshot.value = vals[0] ?? 0
    }
    if (parsed.generation_kwargs?.max_gen_toks) maxTokens.value = parsed.generation_kwargs.max_gen_toks
    sampleLimit.value = parsed.limit ?? null
    showConfigEditor.value = false
  } catch (e) {
    configEditorError.value = e.message
  }
}

onMounted(async () => {
  document.addEventListener('click', onClickOutside)
  presets.value = await listPresets()
  validationErrors.value = []

  if (props.initial?.benchmark_config?.tasks) {
    const tasks = props.initial.benchmark_config.tasks
    const taskIds = new Set()
    for (const t of (Array.isArray(tasks) ? tasks : [tasks])) {
      for (const preset of presets.value) {
        const presetTasks = preset.config?.tasks || []
        if (presetTasks.includes(t) && !taskIds.has(preset.id)) {
          taskIds.add(preset.id)
          selectedPresets.value.push(preset.id)
        }
      }
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
watch(selectedPresets, (ids) => {
  if (ids.length === 0) return
  const selectedPresetsData = ids.map(id => presets.value.find(p => p.id === id)).filter(Boolean)
  if (!selectedPresetsData.length) return

  const allTasks = []
  const fewshotMap = {}
  let genKwargs = null
  let presetMaxTokens = null
  let presetFewshot = null

  for (const p of selectedPresetsData) {
    const tasks = p.config?.tasks || []
    for (const t of (Array.isArray(tasks) ? tasks : [tasks])) {
      if (!allTasks.includes(t)) allTasks.push(t)
    }
    if (p.config?.num_fewshot) {
      Object.assign(fewshotMap, p.config.num_fewshot)
      if (presetFewshot == null) presetFewshot = Object.values(p.config.num_fewshot)[0]
    }
    if (p.config?.generation_kwargs && !genKwargs) {
      genKwargs = p.config.generation_kwargs
      if (genKwargs.max_gen_toks && !presetMaxTokens) presetMaxTokens = genKwargs.max_gen_toks
    }
  }

  const primary = selectedPresetsData[0]
  if (ids.length === 1) {
    form.benchmark.name = primary.name
    form.benchmark.metrics = primary.metrics
  } else {
    form.benchmark.name = selectedPresetsData.map(p => p.name.split(' (')[0]).join(' + ')
    form.benchmark.metrics = null
  }

  form.benchmark.config = {
    tasks: allTasks,
    num_fewshot: fewshotMap,
    limit: null,
    batch_size: 1,
    ...(genKwargs ? { generation_kwargs: genKwargs } : {}),
  }

  if (presetFewshot != null) numFewshot.value = presetFewshot
  if (presetMaxTokens) maxTokens.value = presetMaxTokens
}, { deep: true })

async function handleTestConnection() {
  testing.value = true
  connResult.value = null
  try {
    const payload = {
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
  if (!validate()) return
  const llm = { ...form.llm }
  llm.params = {
    num_concurrent: numConcurrent.value,
    temperature: llmTemperature.value,
    max_tokens: llmMaxTokens.value,
  }
  const payload = {
    name: form.name,
    cron_expr: form.cron_expr,
    llm,
    benchmark: { ...form.benchmark },
    expires_at: expiresAt.value ? new Date(expiresAt.value).toISOString() : null,
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
.hint {
  @apply inline-flex items-center justify-center align-middle text-gray-400 cursor-help relative;
  width: 14px;
  height: 14px;
  margin-left: 2px;
}
.hint::after {
  content: attr(data-hint);
  @apply absolute left-1/2 -translate-x-1/2 bottom-full mb-1.5 bg-gray-800 text-white text-xs font-normal leading-snug rounded py-1.5 px-2.5 whitespace-normal w-max max-w-[220px] opacity-0 pointer-events-none transition-opacity z-50;
}
.hint:hover::after {
  @apply opacity-100;
}
</style>
