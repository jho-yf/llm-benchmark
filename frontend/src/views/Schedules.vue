<template>
  <div class="max-w-[1200px] mx-auto py-6 px-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-gray-800">LLM Benchmark</h1>
      <button @click="showForm = true" class="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
        + 新建定时任务
      </button>
    </div>

    <!-- Schedule Table -->
    <div class="mb-8">
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
          <tr v-for="s in schedules" :key="s.id" class="border-b hover:bg-gray-50">
            <td class="py-2 px-3">{{ s.name }}</td>
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
              <button @click="configSchedule = s"
                class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 hover:bg-gray-200">配置</button>
              <button @click="handleDuplicate(s)"
                class="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700 hover:bg-purple-200">复制</button>
              <button @click="editingSchedule = s; showForm = true" :disabled="isScheduleRunning(s)"
                class="text-xs px-2 py-0.5 rounded bg-yellow-100 text-yellow-700 hover:bg-yellow-200 disabled:opacity-40 disabled:cursor-not-allowed">编辑</button>
              <button @click="handleDelete(s)" :disabled="isScheduleRunning(s)"
                class="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-40 disabled:cursor-not-allowed">删除</button>
            </td>
          </tr>
          <tr v-if="!schedules.length">
            <td colspan="6" class="py-8 text-center text-gray-400">暂无定时任务</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Run History -->
    <div>
      <div class="flex items-center gap-3 mb-3">
        <h2 class="text-base font-semibold text-gray-700">运行记录</h2>
        <button @click="refresh" :disabled="refreshing" class="text-gray-400 hover:text-gray-600 disabled:text-gray-300" title="刷新">
          <svg class="w-4 h-4" :class="refreshing ? 'animate-spin' : ''" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h5M20 20v-5h-5M4.93 9a8 8 0 0113.14 0M19.07 15a8 8 0 01-13.14 0"/></svg>
        </button>
        <select v-model="filterScheduleId" @change="refresh" class="border border-gray-300 rounded px-2 py-1 text-sm">
          <option value="">全部任务</option>
          <option v-for="s in schedules" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
        <select v-model="filterStatus" @change="refresh" class="border border-gray-300 rounded px-2 py-1 text-sm">
          <option value="">全部状态</option>
          <option value="running">运行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
          <option value="cancelled">已终止</option>
        </select>
        <button v-if="selectedRunIds.size > 0" @click="handleDeleteRuns"
          class="ml-auto text-xs px-3 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200">
          删除选中 ({{ selectedRunIds.size }})
        </button>
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
              <span v-if="r.status === 'running' && r.progress" class="ml-1 text-xs text-blue-600 font-mono">{{ r.progress }}</span>
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

    <!-- Config Modal -->
    <div v-if="configSchedule" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="configSchedule = null">
      <div class="bg-white rounded-lg shadow-xl w-[700px] max-h-[85vh] overflow-y-auto">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <h2 class="text-lg font-semibold text-gray-800">{{ configSchedule.name }} — 任务配置</h2>
          <button @click="configSchedule = null" class="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <div class="px-6 py-4 space-y-5 text-sm">
          <!-- Basic -->
          <div>
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">基本信息</h3>
            <div class="grid grid-cols-2 gap-3">
              <div><span class="text-gray-500">名称：</span>{{ configSchedule.name }}</div>
              <div><span class="text-gray-500">Cron：</span><code class="bg-gray-100 px-1 rounded">{{ configSchedule.cron_expr }}</code></div>
              <div><span class="text-gray-500">状态：</span>{{ configSchedule.enabled ? '启用' : '停用' }}</div>
              <div><span class="text-gray-500">创建时间：</span>{{ formatDt(configSchedule.created_at) }}</div>
            </div>
          </div>
          <!-- LLM -->
          <div>
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">模型配置</h3>
            <div class="grid grid-cols-2 gap-3">
              <div><span class="text-gray-500">提供商：</span>{{ configSchedule.llm_provider }}</div>
              <div><span class="text-gray-500">模型：</span>{{ configSchedule.llm_model_id }}</div>
              <div class="col-span-2"><span class="text-gray-500">API 地址：</span>{{ configSchedule.llm_api_base }}</div>
              <div><span class="text-gray-500">认证方式：</span>{{ configSchedule.llm_auth_type }}</div>
              <div><span class="text-gray-500">密钥：</span>{{ configSchedule.llm_api_key ? '••••••••' : '未设置' }}</div>
            </div>
            <div v-if="configSchedule.llm_params" class="mt-2">
              <span class="text-gray-500">参数：</span>
              <pre class="mt-1 bg-gray-50 border rounded p-2 text-xs font-mono overflow-x-auto">{{ JSON.stringify(configSchedule.llm_params, null, 2) }}</pre>
            </div>
          </div>
          <!-- Benchmark -->
          <div>
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Benchmark 配置</h3>
            <div class="grid grid-cols-2 gap-3">
              <div><span class="text-gray-500">名称：</span>{{ configSchedule.benchmark_name }}</div>
              <div><span class="text-gray-500">分类：</span>{{ configSchedule.benchmark_category }}</div>
            </div>
            <div class="mt-2">
              <span class="text-gray-500">评测配置：</span>
              <pre class="mt-1 bg-gray-50 border rounded p-2 text-xs font-mono overflow-x-auto">{{ JSON.stringify(configSchedule.benchmark_config, null, 2) }}</pre>
            </div>
            <div v-if="configSchedule.benchmark_metrics" class="mt-2">
              <span class="text-gray-500">指标：</span>
              <pre class="mt-1 bg-gray-50 border rounded p-2 text-xs font-mono overflow-x-auto">{{ JSON.stringify(configSchedule.benchmark_metrics, null, 2) }}</pre>
            </div>
            <div v-if="configSchedule.benchmark_params" class="mt-2">
              <span class="text-gray-500">运行参数：</span>
              <pre class="mt-1 bg-gray-50 border rounded p-2 text-xs font-mono overflow-x-auto">{{ JSON.stringify(configSchedule.benchmark_params, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Form Modal -->
    <ScheduleForm
      v-if="showForm"
      :initial="editingSchedule"
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
          <div class="h-full bg-blue-500 transition-all duration-300" :style="{ width: logProgressPct + '%' }"></div>
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
          <!-- Metrics Table -->
          <table v-if="reportMetrics.length" class="w-full text-sm border-collapse">
            <thead>
              <tr class="border-b text-left text-gray-500">
                <th class="py-2 px-3">Task</th>
                <th class="py-2 px-3">Metric</th>
                <th class="py-2 px-3 text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, i) in reportMetrics" :key="i" class="border-b hover:bg-gray-50">
                <td class="py-2 px-3 font-mono">{{ m.task }}</td>
                <td class="py-2 px-3">{{ m.key }}</td>
                <td class="py-2 px-3 text-right font-mono font-semibold" :class="m.key.includes('acc') || m.key.includes('score') ? 'text-green-600' : ''">{{ m.value }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-center text-gray-400 py-8">无结果数据</div>
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
const configSchedule = ref(null)
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
let logEventSource = null

const isAllSelected = computed(() => {
  const selectable = runs.value.filter(r => r.status !== 'running')
  return selectable.length > 0 && selectable.every(r => selectedRunIds.value.has(r.id))
})

const reportMetrics = computed(() => {
  if (!reportRun.value?.result) return []
  const rows = []
  const results = reportRun.value.result.results || reportRun.value.result
  for (const [task, metrics] of Object.entries(results)) {
    if (typeof metrics !== 'object') continue
    for (const [k, v] of Object.entries(metrics)) {
      if (typeof v === 'number') rows.push({ task, key: k, value: v.toFixed(4) })
    }
  }
  return rows
})

watch(logLines, () => {
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
  })
})

function isScheduleRunning(s) {
  return allRunningJobIds.value.has(s.id)
}

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

onMounted(refresh)

onUnmounted(() => {
  closeLog()
})

function closeForm() {
  showForm.value = false
  editingSchedule.value = null
}

async function handleSave(payload) {
  if (editingSchedule.value) {
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
  const progressRe = /(\d+)\/(\d+)/
  logEventSource = new EventSource(`/api/runs/${runId}/log`)
  logEventSource.onmessage = (e) => {
    logLines.value.push(e.data + '\n')
    if (logLines.value.length > 500) logLines.value.splice(0, 100)
    const m = progressRe.exec(e.data)
    if (m) {
      logProgress.value = `${m[1]}/${m[2]}`
      logProgressPct.value = Math.round((parseInt(m[1]) / parseInt(m[2])) * 100)
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
  const end = r.finished_at ? new Date(r.finished_at) : new Date()
  const ms = end - new Date(r.started_at)
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  return `${Math.round(ms / 60000)}min`
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

function showError(r) {
  const msg = r.result?.error || JSON.stringify(r.result, null, 2) || '无详情'
  errorMessage.value = msg
}

function showReport(r) {
  reportRun.value = r
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
