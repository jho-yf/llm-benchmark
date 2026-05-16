<template>
  <div class="max-w-[1200px] mx-auto py-6 px-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-gray-800">LLM Benchmark</h1>
      <button @click="showForm = true; formReadonly = false; editingSchedule = null" class="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
        + 新建定时任务
      </button>
    </div>

    <!-- Schedule Table -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-3">
        <h2 class="text-base font-semibold text-gray-700">任务列表</h2>
        <select v-model="filterScheduleModel" class="ml-auto border border-gray-300 rounded px-2 py-1 text-sm">
          <option value="">全部模型</option>
          <option v-for="m in scheduleModels" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b text-left text-gray-500">
            <th class="py-2 px-3">名称</th>
            <th class="py-2 px-3">模型</th>
            <th class="py-2 px-3">Benchmark</th>
            <th class="py-2 px-3">Cron</th>
            <th class="py-2 px-3">状态</th>
            <th class="py-2 px-3">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filteredSchedules" :key="s.id"
            class="border-b hover:bg-gray-50 cursor-pointer"
            :class="filterScheduleId === s.id ? 'bg-blue-50' : ''"
            @click="selectSchedule(s)">
            <td class="py-2 px-3">
              <div class="flex items-center gap-1.5">
                <button @click.stop="handleDuplicate(s)" title="复制" class="text-gray-300 hover:text-purple-600 shrink-0">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                </button>
                <span>{{ s.name }}</span>
              </div>
            </td>
            <td class="py-2 px-3">{{ s.llm_model_id }}</td>
            <td class="py-2 px-3">{{ s.benchmark_name }}</td>
            <td class="py-2 px-3 font-mono text-xs relative group">
                {{ s.cron_expr }}
                <div v-if="s.enabled && getNextRuns(s.cron_expr).length"
                  class="absolute left-0 top-full z-10 mt-1 bg-gray-800 text-white text-xs rounded py-2 px-3 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                  <div class="font-semibold text-gray-300 mb-1">接下来 5 次运行</div>
                  <div v-for="d in getNextRuns(s.cron_expr)" :key="d">{{ d }}</div>
                </div>
              </td>
            <td class="py-2 px-3">
              <button @click="handleToggle(s)" class="text-xs px-2 py-0.5 rounded"
                :class="s.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'">
                {{ s.enabled ? '启用' : '停用' }}
              </button>
            </td>
            <td class="py-2 px-3 space-x-1">
              <button @click="handleTrigger(s)" :disabled="isScheduleRunning(s)"
                class="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-40 disabled:cursor-not-allowed">触发</button>
              <button @click="openScheduleForm(s)"
                class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 hover:bg-gray-200">{{ isScheduleRunning(s) ? '查看' : '编辑' }}</button>
              <button @click="handleDelete(s)" :disabled="isScheduleRunning(s)"
                class="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-40 disabled:cursor-not-allowed">删除</button>
            </td>
          </tr>
          <tr v-if="!filteredSchedules.length">
            <td colspan="6" class="py-8 text-center text-gray-400">暂无定时任务</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Run History -->
    <div>
      <div class="flex items-center gap-3 mb-3">
        <h2 class="text-base font-semibold text-gray-700">运行记录</h2>
        <span v-if="selectedScheduleName" class="text-sm text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
          {{ selectedScheduleName }}
          <button @click="clearScheduleFilter" class="ml-1 text-blue-400 hover:text-blue-600">&times;</button>
        </span>
        <button @click="refresh" :disabled="refreshing" class="text-gray-400 hover:text-gray-600 disabled:text-gray-300" title="刷新">
          <svg class="w-4 h-4" :class="refreshing ? 'animate-spin' : ''" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h5M20 20v-5h-5M4.93 9a8 8 0 0113.14 0M19.07 15a8 8 0 01-13.14 0"/></svg>
        </button>
        <label class="flex items-center gap-1 text-xs text-gray-500 cursor-pointer select-none">
          <input type="checkbox" v-model="autoRefresh" class="accent-blue-600" />
          自动刷新
        </label>
        <div class="ml-auto flex items-center gap-3">
          <select v-model="filterStatus" @change="refresh" class="border border-gray-300 rounded px-2 py-1 text-sm">
            <option value="">全部状态</option>
            <option value="running">运行中</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
            <option value="cancelled">已终止</option>
          </select>
          <button v-if="selectedRunIds.size > 0" @click="handleDeleteRuns"
            class="text-xs px-3 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200">
            删除选中 ({{ selectedRunIds.size }})
          </button>
        </div>
      </div>
      <table class="w-full text-sm table-fixed">
        <colgroup>
          <col class="w-[36px]" />
          <col class="w-[180px]" />
          <col class="w-[200px]" />
          <col class="w-[100px]" />
          <col class="w-[60px]" />
          <col class="w-[80px]" />
          <col />
          <col class="w-[110px]" />
        </colgroup>
        <thead>
          <tr class="border-b text-left text-gray-500">
            <th class="py-2 px-3"><input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" /></th>
            <th class="py-2 px-3">模型</th>
            <th class="py-2 px-3">Benchmark</th>
            <th class="py-2 px-3">开始</th>
            <th class="py-2 px-3">耗时</th>
            <th class="py-2 px-3">状态</th>
            <th class="py-2 px-3">结果</th>
            <th class="py-2 px-3">操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="r in runs" :key="r.id">
          <tr class="border-b hover:bg-gray-50">
            <td class="py-2 px-3"><input type="checkbox" :disabled="r.status === 'running'" :checked="selectedRunIds.has(r.id)" @change="toggleRunSelect(r.id)" /></td>
            <td class="py-2 px-3 truncate" :title="r.llm_model_id">{{ r.llm_model_id || '-' }}</td>
            <td class="py-2 px-3 truncate" :title="r.benchmark_name">{{ r.benchmark_name || '-' }}</td>
            <td class="py-2 px-3 text-xs text-gray-500">{{ formatDt(r.started_at) }}</td>
            <td class="py-2 px-3 text-xs">{{ duration(r) }}</td>
            <td class="py-2 px-3">
              <StatusBadge :status="r.status" />
              <div v-if="r.status === 'running' && r.progress" class="mt-1">
                <div class="flex items-center gap-1.5">
                  <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full transition-all duration-300" :style="{ width: calcProgressPct(r.progress) + '%' }"></div>
                  </div>
                  <span class="text-xs text-blue-600 font-mono whitespace-nowrap">{{ formatProgress(r.progress) }}</span>
                </div>
              </div>
            </td>
            <td class="py-2 px-3 text-xs font-mono truncate max-w-[200px]" :title="formatResultFull(r.result)">
              <span v-if="r.status === 'failed'" class="cursor-pointer text-red-600 underline" @click="showError(r)">{{ formatError(r.result) }}</span>
              <span v-else>{{ formatResult(r.result) }}</span>
            </td>
            <td class="py-2 px-3 space-x-1">
              <button v-if="r.status === 'completed'" @click="showReport(r)"
                class="text-xs px-2 py-0.5 rounded bg-green-100 text-green-700 hover:bg-green-200">报告</button>
              <button v-if="r.status === 'running'" @click="toggleLog(r.id)"
                class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 hover:bg-gray-200">日志</button>
              <button v-if="r.status === 'running'" @click="handleCancelRun(r.id)"
                class="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-700 hover:bg-orange-200">终止</button>
            </td>
          </tr>
          </template>
          <tr v-if="!runs.length">
            <td colspan="8" class="py-8 text-center text-gray-400">暂无运行记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Form Modal -->
    <ScheduleForm
      v-if="showForm"
      :initial="editingSchedule"
      :readonly="formReadonly"
      @save="handleSave"
      @cancel="closeForm"
    />

    <!-- Error Modal -->
    <div v-if="errorMessage" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="errorMessage = null">
      <div class="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] overflow-y-auto p-6">
        <h2 class="text-lg font-semibold text-red-600 mb-3">运行失败详情</h2>
        <pre class="bg-gray-50 border rounded p-4 text-xs text-gray-700 whitespace-pre-wrap break-all">{{ errorMessage }}</pre>
        <div class="flex justify-end mt-4">
          <button @click="errorMessage = null" class="px-4 py-2 border rounded hover:bg-gray-50">关闭</button>
        </div>
      </div>
    </div>

    <!-- Log Modal -->
    <div v-if="expandedLogId" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="closeLog">
      <div class="bg-gray-900 rounded-lg shadow-xl w-[1100px] max-h-[85vh] flex flex-col">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-700">
          <div class="flex items-center gap-3">
            <h2 class="text-base font-medium text-gray-200">运行日志</h2>
            <span v-if="logProgress" class="text-sm text-blue-400 font-mono">{{ logProgress }}</span>
          </div>
          <button @click="closeLog" class="text-gray-400 hover:text-white text-xl leading-none">&times;</button>
        </div>
        <div v-if="logProgressPct >= 0" class="h-1.5 bg-gray-800">
          <div class="h-full bg-blue-500 rounded-r transition-all duration-500" :style="{ width: logProgressPct + '%' }"></div>
        </div>
        <pre ref="logContainer" class="flex-1 overflow-y-auto p-5 text-sm text-green-300 whitespace-pre-wrap font-mono">{{ logLines.join('') || '等待日志...' }}</pre>
      </div>
    </div>

    <!-- Report Modal -->
    <div v-if="reportRun" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="reportRun = null">
      <div class="bg-white rounded-lg shadow-xl w-[700px] max-h-[85vh] overflow-y-auto">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <h2 class="text-lg font-semibold text-gray-800">Benchmark 报告</h2>
          <button @click="reportRun = null" class="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <div class="px-6 py-4 space-y-4">
          <!-- Summary -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-500">模型：</span>{{ reportRun.llm_model_id || '-' }}</div>
            <div><span class="text-gray-500">Benchmark：</span>{{ reportRun.benchmark_name || '-' }}</div>
            <div><span class="text-gray-500">开始时间：</span>{{ formatDt(reportRun.started_at) }}</div>
            <div><span class="text-gray-500">耗时：</span>{{ duration(reportRun) }}</div>
          </div>
          <!-- Token Usage -->
          <div v-if="reportTokenUsage" class="bg-gray-50 border rounded p-3">
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Token 消耗</h3>
            <div class="grid grid-cols-3 gap-3 text-sm">
              <div>
                <div class="text-2xl font-bold text-blue-600 font-mono">{{ formatNumber(reportTokenUsage.prompt_tokens) }}</div>
                <div class="text-xs text-gray-400">Prompt Tokens</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-green-600 font-mono">{{ formatNumber(reportTokenUsage.completion_tokens) }}</div>
                <div class="text-xs text-gray-400">Completion Tokens</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-purple-600 font-mono">{{ formatNumber(reportTokenUsage.total_tokens) }}</div>
                <div class="text-xs text-gray-400">Total Tokens</div>
              </div>
            </div>
          </div>
          <!-- Per-Task Details -->
          <div v-for="detail in reportTaskDetails" :key="detail.name" class="border rounded">
            <div class="flex items-center justify-between bg-gray-50 px-3 py-2 cursor-pointer" @click="detail._expanded = !detail._expanded">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-gray-700 font-mono">{{ detail.name }}</span>
                <span v-if="detail.nShot != null" class="text-xs bg-blue-100 text-blue-600 px-1.5 rounded">{{ detail.nShot }}-shot</span>
                <span v-if="detail.nSamples" class="text-xs text-gray-400">{{ detail.nSamples }} 样本</span>
              </div>
              <span class="text-gray-400 text-xs">{{ detail._expanded ? '收起' : '展开' }}</span>
            </div>
            <div v-if="detail._expanded" class="px-3 py-2 space-y-2 text-sm">
              <!-- Metrics -->
              <table v-if="detail.metrics.length" class="w-full">
                <thead>
                  <tr class="border-b text-left text-gray-500 text-xs">
                    <th class="py-1 px-2">指标</th>
                    <th class="py-1 px-2 text-right">值</th>
                    <th class="py-1 px-2 w-[40%]">说明</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="m in detail.metrics" :key="m.key" class="border-b last:border-0">
                    <td class="py-1 px-2 text-xs font-medium">{{ m.key }}</td>
                    <td class="py-1 px-2 text-right font-mono font-semibold text-xs" :class="m.highlight ? 'text-green-600' : ''">{{ m.value }}</td>
                    <td class="py-1 px-2 text-xs text-gray-400">{{ metricDesc(m.key) }}</td>
                  </tr>
                </tbody>
              </table>
              <!-- Config -->
              <div v-if="detail.config && Object.keys(detail.config).length">
                <div class="text-xs text-gray-400 mb-1">配置</div>
                <pre class="bg-gray-50 rounded p-2 text-xs font-mono overflow-x-auto max-h-40">{{ JSON.stringify(detail.config, null, 2) }}</pre>
              </div>
            </div>
          </div>
          <div v-if="!reportTaskDetails.length" class="text-center text-gray-400 py-8">无结果数据</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import ScheduleForm from '../components/ScheduleForm.vue'
import { Cron } from 'croner'
import {
  listSchedules, createSchedule, updateSchedule,
  deleteSchedule, toggleSchedule, triggerSchedule, listRuns, deleteRuns, cancelRun,
} from '../api'

const schedules = ref([])
const runs = ref([])
const allRunningJobIds = ref(new Set())
const showForm = ref(false)
const editingSchedule = ref(null)
const formReadonly = ref(false)
const errorMessage = ref(null)
const reportRun = ref(null)
const selectedRunIds = ref(new Set())
const expandedLogId = ref(null)
const logLines = ref([])
const logContainer = ref(null)
const logProgress = ref('')
const logProgressPct = ref(-1)
const refreshing = ref(false)
const filterScheduleId = ref('')
const filterStatus = ref('')
const filterScheduleModel = ref('')
const autoRefresh = ref(true)
let logEventSource = null

const scheduleModels = computed(() => {
  const models = new Set()
  for (const s of schedules.value) {
    if (s.llm_model_id) models.add(s.llm_model_id)
  }
  return [...models].sort()
})

const filteredSchedules = computed(() => {
  if (!filterScheduleModel.value) return schedules.value
  return schedules.value.filter(s => s.llm_model_id === filterScheduleModel.value)
})
let autoRefreshTimer = null

const isAllSelected = computed(() => {
  const selectable = runs.value.filter(r => r.status !== 'running')
  return selectable.length > 0 && selectable.every(r => selectedRunIds.value.has(r.id))
})

const reportTokenUsage = computed(() => {
  if (!reportRun.value?.result) return null
  const usage = reportRun.value.result.token_usage
  if (!usage || (!usage.prompt_tokens && !usage.completion_tokens)) return null
  return usage
})

const _metricDescs = {
  exact_match: '精确匹配准确率，模型输出与标准答案完全一致的占比',
  acc: '准确率，正确回答占总样本的百分比',
  acc_norm: '长度归一化准确率，排除答案长度偏差后的准确率',
  pass: '代码通过率',
  'pass@1': '单次生成通过率，生成一次代码即通过测试的概率',
  score: '综合得分',
  qa_f1_score: 'QA F1 分数，基于词级别的精确率和召回率的调和平均',
  bleu_acc: 'BLEU 准确率，基于 BLEU 分数阈值判断回答是否正确',
  rouge1_acc: 'ROUGE-1 准确率，基于 unigram 重叠度判断回答正确性',
  prompt_level_strict_acc: '严格指令遵循率，所有约束均满足的 prompt 占比',
  prompt_level_loose_acc: '宽松指令遵循率，满足大部分约束的 prompt 占比',
  inst_level_strict_acc: '严格指令级准确率，每条指令是否被严格遵循',
  inst_level_loose_acc: '宽松指令级准确率，每条指令是否被宽松遵循',
}

function metricDesc(key) {
  if (_metricDescs[key]) return _metricDescs[key]
  if (key.includes('exact_match') || key.includes('em')) return '精确匹配准确率'
  if (key.includes('acc') && key.includes('norm')) return '长度归一化准确率'
  if (key.includes('acc')) return '准确率'
  if (key.includes('pass')) return '代码通过率'
  if (key.includes('f1')) return 'F1 分数，精确率与召回率的调和平均'
  if (key.includes('bleu')) return 'BLEU 分数，衡量生成文本与参考文本的 n-gram 匹配度'
  if (key.includes('rouge')) return 'ROUGE 分数，衡量生成文本与参考文本的重叠度'
  return ''
}

const _keyMetrics = ['exact_match', 'acc', 'pass@1', 'score', 'prompt_level_strict_acc']

const reportTaskDetails = computed(() => {
  if (!reportRun.value?.result) return []
  const result = reportRun.value.result
  const results = result.results || {}
  const configs = result.configs || result['n-samples'] ? result.configs || {} : {}
  const nSamples = result['n-samples'] || {}
  const nShot = result['n-shot'] || {}

  const tasks = []
  for (const [taskName, metrics] of Object.entries(results)) {
    if (typeof metrics !== 'object') continue
    const taskMetrics = []
    for (const [k, v] of Object.entries(metrics)) {
      if (typeof v === 'number') {
        const highlight = _keyMetrics.some(m => k.includes(m))
        taskMetrics.push({ key: k, value: v.toFixed(4), highlight })
      }
    }
    if (!taskMetrics.length) continue
    tasks.push({
      name: taskName,
      metrics: taskMetrics,
      config: configs[taskName] || null,
      nSamples: nSamples[taskName]?.original || nSamples[taskName]?.effective || null,
      nShot: nShot[taskName] ?? null,
      _expanded: tasks.length < 5,
    })
  }
  return tasks
})

watch(logLines, () => {
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
  })
})

function isScheduleRunning(s) {
  return allRunningJobIds.value.has(s.id)
}

function selectSchedule(s) {
  if (filterScheduleId.value === s.id) {
    filterScheduleId.value = ''
  } else {
    filterScheduleId.value = s.id
  }
  refresh()
}

function clearScheduleFilter() {
  filterScheduleId.value = ''
  refresh()
}

const selectedScheduleName = computed(() => {
  if (!filterScheduleId.value) return ''
  const s = schedules.value.find(x => x.id === filterScheduleId.value)
  return s ? s.name : ''
})

async function refresh() {
  refreshing.value = true
  try {
  const params = {}
  if (filterScheduleId.value) params.job_id = filterScheduleId.value
  if (filterStatus.value) params.status = filterStatus.value
  const [s, r, allRuns] = await Promise.all([
    listSchedules(),
    listRuns(params),
    listRuns({ status: 'running' }),
  ])
  schedules.value = s
  runs.value = r
  allRunningJobIds.value = new Set(allRuns.filter(x => x.status === 'running').map(x => x.scheduled_job_id))
  selectedRunIds.value = new Set()
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  refresh()
  autoRefreshTimer = setInterval(() => {
    if (autoRefresh.value) refresh()
  }, 5000)
})

onUnmounted(() => {
  closeLog()
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
})

function closeForm() {
  showForm.value = false
  editingSchedule.value = null
  formReadonly.value = false
}

function openScheduleForm(s) {
  editingSchedule.value = s
  formReadonly.value = isScheduleRunning(s)
  showForm.value = true
}

async function handleSave(payload) {
  if (editingSchedule.value?.id) {
    await updateSchedule(editingSchedule.value.id, payload)
  } else {
    await createSchedule(payload)
  }
  closeForm()
  await refresh()
}

async function handleToggle(s) {
  await toggleSchedule(s.id)
  await refresh()
}

async function handleTrigger(s) {
  await triggerSchedule(s.id)
  await refresh()
}

function handleDuplicate(s) {
  editingSchedule.value = {
    ...s,
    name: s.name + ' (副本)',
    llm_api_key: '',
    id: null,
  }
  showForm.value = true
}

async function handleDelete(s) {
  if (!confirm(`确定删除「${s.name}」？`)) return
  await deleteSchedule(s.id)
  await refresh()
}

function toggleRunSelect(id) {
  const next = new Set(selectedRunIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedRunIds.value = next
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedRunIds.value = new Set()
  } else {
    selectedRunIds.value = new Set(runs.value.filter(r => r.status !== 'running').map(r => r.id))
  }
}

async function handleDeleteRuns() {
  if (!confirm(`确定删除选中的 ${selectedRunIds.value.size} 条运行记录？`)) return
  await deleteRuns([...selectedRunIds.value])
  selectedRunIds.value = new Set()
  await refresh()
}

async function handleCancelRun(id) {
  await cancelRun(id)
  closeLog()
  await refresh()
}

function toggleLog(runId) {
  if (expandedLogId.value === runId) {
    closeLog()
    return
  }
  closeLog()
  expandedLogId.value = runId
  logLines.value = []
  logProgress.value = ''
  logProgressPct.value = -1
  const numRe = /(\d+)\/(\d+)/
  const bmRe = /\[benchmark (\d+)\/(\d+)\]\s+(\S+)(?:\s+(\S+))?/
  logEventSource = new EventSource(`/api/runs/${runId}/log`)
  logEventSource.onmessage = (e) => {
    const line = e.data
    logLines.value.push(line + '\n')
    if (logLines.value.length > 500) logLines.value.splice(0, 100)
    const bm = bmRe.exec(line)
    if (bm) {
      const bmIdx = bm[1]
      const bmTotal = bm[2]
      const name = _taskNames[bm[3]] || bm[3]
      const stage = bm[4] || ''
      const stageLabel = _stageNames[stage] || ''
      const nm = numRe.exec(line)
      if (nm) {
        logProgress.value = bmTotal !== '1' ? `${name} (${bmIdx}/${bmTotal}) 推理 ${nm[1]}/${nm[2]}` : `${name} 推理 ${nm[1]}/${nm[2]}`
        const taskPct = parseInt(nm[1]) / parseInt(nm[2])
        const perBm = 100 / parseInt(bmTotal)
        logProgressPct.value = Math.min(100, Math.round(((parseInt(bmIdx) - 1) + taskPct) * perBm))
      } else if (stageLabel) {
        logProgress.value = bmTotal !== '1' ? `${name} (${bmIdx}/${bmTotal}) ${stageLabel}` : `${name} ${stageLabel}`
        const taskPct = stage === 'done' ? 1 : (stage === 'loading' ? 0.05 : 0.1)
        const perBm = 100 / parseInt(bmTotal)
        logProgressPct.value = Math.min(100, Math.round(((parseInt(bmIdx) - 1) + taskPct) * perBm))
      }
    } else {
      const nm = numRe.exec(line)
      if (nm) {
        logProgress.value = `${nm[1]}/${nm[2]}`
        logProgressPct.value = Math.round((parseInt(nm[1]) / parseInt(nm[2])) * 100)
      }
    }
  }
  logEventSource.onerror = () => {
    if (logEventSource) {
      logEventSource.close()
      logEventSource = null
    }
  }
}

function closeLog() {
  if (logEventSource) {
    logEventSource.close()
    logEventSource = null
  }
  expandedLogId.value = null
  logLines.value = []
  logProgress.value = ''
  logProgressPct.value = -1
}

function formatDt(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function duration(r) {
  if (!r.started_at) return '-'
  const start = new Date(r.started_at)
  const end = r.finished_at ? new Date(r.finished_at) : new Date()
  let ms = end - start
  if (ms < 0) ms = 0
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  if (ms < 3600000) return `${Math.round(ms / 60000)}min`
  const h = Math.floor(ms / 3600000)
  const m = Math.round((ms % 3600000) / 60000)
  return `${h}h${m > 0 ? m + 'min' : ''}`
}

function formatResult(result) {
  if (!result) return '-'
  const parts = []
  for (const [task, metrics] of Object.entries(result.results || result)) {
    if (typeof metrics === 'object') {
      for (const [k, v] of Object.entries(metrics)) {
        if (typeof v === 'number') parts.push(`${k}=${v.toFixed(3)}`)
      }
    }
  }
  return parts.slice(0, 2).join(', ') || '-'
}

function formatResultFull(result) {
  if (!result) return ''
  const parts = []
  for (const [task, metrics] of Object.entries(result.results || result)) {
    if (typeof metrics === 'object') {
      for (const [k, v] of Object.entries(metrics)) {
        if (typeof v === 'number') parts.push(`${k}=${v.toFixed(4)}`)
      }
    }
  }
  return parts.join(', ')
}

function formatError(result) {
  if (!result) return '未知错误'
  return result.error || JSON.stringify(result).slice(0, 80)
}

const _taskNames = {
  gsm8k: 'GSM8K',
  humaneval: 'HumanEval',
  mmlu_generative: 'MMLU',
  ceval_gen: 'C-Eval',
  longbench: 'LongBench',
  longbench_2wikimqa: 'LongBench-2WikiMQA',
  longbench_dureader: 'LongBench-DuReader',
  longbench_gov_report: 'LongBench-GovReport',
  longbench_hotpotqa: 'LongBench-HotpotQA',
  longbench_lcc: 'LongBench-LCC',
  longbench_multi_news: 'LongBench-MultiNews',
  longbench_multifieldqa_en: 'LongBench-MFQA-en',
  longbench_multifieldqa_zh: 'LongBench-MFQA-zh',
  longbench_musique: 'LongBench-MuSiQue',
  longbench_narrativeqa: 'LongBench-NarrativeQA',
  longbench_passage_count: 'LongBench-PassageCount',
  longbench_passage_retrieval_en: 'LongBench-PR-en',
  longbench_passage_retrieval_zh: 'LongBench-PR-zh',
  longbench_qasper: 'LongBench-Qasper',
  longbench_qmsum: 'LongBench-QMSum',
  longbench_repobench: 'LongBench-RepoBench',
  longbench_samsum: 'LongBench-SamSum',
  longbench_trec: 'LongBench-TREC',
  longbench_triviaqa: 'LongBench-TriviaQA',
  longbench_vcsum: 'LongBench-VCSum',
}

const _stageNames = { loading: '加载中', running: '推理中', done: '计算指标', failed: '失败' }

function formatProgress(progress) {
  if (!progress) return ''
  const colonIdx = progress.indexOf(':')
  if (colonIdx !== -1) {
    const prefix = progress.slice(0, colonIdx).trim()
    const num = progress.slice(colonIdx + 1).trim()
    const idxMatch = prefix.match(/^\((\d+)\/(\d+)\)\s*(.*)/)
    if (idxMatch) {
      const name = _taskNames[idxMatch[3]] || idxMatch[3]
      return `${name} (${idxMatch[1]}/${idxMatch[2]}) 推理 ${num}`
    }
    const totalMatch = prefix.match(/^\((\d+)\)\s*(.*)/)
    if (totalMatch) {
      const name = _taskNames[totalMatch[2]] || totalMatch[2]
      return `${name} (${totalMatch[1]}) 推理 ${num}`
    }
    const name = _taskNames[prefix] || prefix
    return `${name} 推理 ${num}`
  }
  // Stage format: "(1/3) gsm8k loading" or "(3) gsm8k loading" or "gsm8k running"
  const stageMatch = progress.match(/^(?:\((\d+)\/(\d+)\)\s*|\((\d+)\)\s*)?(\S+)\s+(\S+)$/)
  if (stageMatch) {
    const idx = stageMatch[1] || stageMatch[3]
    const total = stageMatch[2] || stageMatch[3]
    const name = _taskNames[stageMatch[4]] || stageMatch[4]
    const stage = _stageNames[stageMatch[5]] || stageMatch[5]
    return idx && total ? `${name} (${idx}/${total}) ${stage}` : `${name} ${stage}`
  }
  return progress
}

function calcProgressPct(progress) {
  if (!progress) return 0
  // Parse benchmark index/total: "(1/3)" or "(3)"
  const idxMatch = progress.match(/\((\d+)\/(\d+)\)/)
  const totalOnlyMatch = progress.match(/\((\d+)\)/)
  const bmIdx = idxMatch ? parseInt(idxMatch[1]) : 1
  const bmTotal = idxMatch ? parseInt(idxMatch[2]) : (totalOnlyMatch ? parseInt(totalOnlyMatch[1]) : 1)
  // Parse numeric task progress
  const numMatch = progress.match(/(\d+)\/(\d+)/)
  let taskPct = 0
  if (numMatch) {
    taskPct = parseInt(numMatch[1]) / parseInt(numMatch[2])
  } else {
    const stageM = progress.match(/\S+\s+(\S+)$/)
    if (stageM) {
      const stage = stageM[1]
      if (stage === 'loading') taskPct = 0.05
      else if (stage === 'running') taskPct = 0.1
      else if (stage === 'done') taskPct = 1
    }
  }
  if (bmTotal <= 1) return Math.round(taskPct * 100)
  const perBm = 100 / bmTotal
  return Math.min(100, Math.round(((bmIdx - 1) + taskPct) * perBm))
}

function showError(r) {
  const msg = r.result?.error || JSON.stringify(r.result, null, 2) || '无详情'
  errorMessage.value = msg
}

function showReport(r) {
  reportRun.value = r
}

function formatNumber(n) {
  if (n == null) return '-'
  return n.toLocaleString()
}

const _nextRunsCache = new Map()
function getNextRuns(cronExpr) {
  if (_nextRunsCache.has(cronExpr)) return _nextRunsCache.get(cronExpr)
  try {
    const job = new Cron(cronExpr)
    const runs = []
    let next = new Date()
    for (let i = 0; i < 5; i++) {
      next = job.nextRun(next)
      if (!next) break
      runs.push(next.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short' }))
      next = new Date(next.getTime() + 1000)
    }
    _nextRunsCache.set(cronExpr, runs)
    return runs
  } catch {
    return []
  }
}
</script>
