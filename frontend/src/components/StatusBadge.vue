<template>
  <span :class="cls">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String })

const map = {
  pending:   { label: '待执行', cls: 'bg-gray-100 text-gray-600' },
  running:   { label: '运行中', cls: 'bg-blue-100 text-blue-700' },
  completed: { label: '已完成', cls: 'bg-green-100 text-green-700' },
  failed:    { label: '失败',   cls: 'bg-red-100 text-red-700' },
  cancelled: { label: '已终止', cls: 'bg-orange-100 text-orange-700' },
}

const label = computed(() => map[props.status]?.label ?? props.status)
const cls = computed(() => [
  'inline-block px-2 py-0.5 text-xs font-medium rounded',
  map[props.status]?.cls ?? 'bg-gray-100 text-gray-600',
])
</script>
