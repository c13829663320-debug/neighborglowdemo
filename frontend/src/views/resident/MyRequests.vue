<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.push('/resident')" class="btn-back">← 首页</button>
      <h1>我的案例</h1>
      <span></span>
    </header>
    <main class="main-content">
      <!-- Filter tabs -->
      <div class="filter-tabs">
        <button v-for="f in filters" :key="f.key" :class="['tab', { active: activeFilter === f.key }]" @click="activeFilter = f.key">
          {{ f.label }}
        </button>
      </div>
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="filteredCases.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <p>暂无{{ activeFilter === 'all' ? '' : filters.find(f=>f.key===activeFilter)?.label }}案例</p>
        <button @click="$router.push('/resident')" class="btn-link">去记录一个问题 →</button>
      </div>
      <div v-else class="case-list">
        <div v-for="c in filteredCases" :key="c.id" class="case-card clickable" :class="'risk-' + c.risk_level" @click="$router.push('/resident/case/' + c.id)">
          <div class="case-header">
            <span class="risk-dot" :class="'dot-' + c.risk_level"></span>
            <span class="case-title">{{ c.title }}</span>
          </div>
          <p class="case-desc">{{ c.description?.slice(0, 80) }}{{ c.description?.length > 80 ? '...' : '' }}</p>
          <div class="case-meta">
            <span class="status-tag" :class="'status-' + c.status">{{ statusLabel(c.status) }}</span>
            <span class="risk-text" :class="'risk-' + c.risk_level">{{ riskLabel(c.risk_level) }}</span>
            <span class="case-date">{{ formatDate(c.created_at) }}</span>
          </div>
          <!-- Progress indicator -->
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getProgress(c.status) + '%' }"></div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { cases } from '../../api'

const casesList = ref([])
const loading = ref(true)
const activeFilter = ref('all')

const filters = [
  { key: 'all', label: '全部' },
  { key: 'draft', label: '待诊断' },
  { key: 'diagnosed', label: '已诊断' },
  { key: 'in_progress', label: '进行中' },
  { key: 'resolved', label: '已解决' },
]

const filteredCases = computed(() => {
  if (activeFilter.value === 'all') return casesList.value
  return casesList.value.filter(c => c.status === activeFilter.value)
})

onMounted(async () => {
  try {
    const res = await cases.list()
    casesList.value = res.data || []
  } catch (e) {
    console.error('Failed to load cases', e)
  } finally {
    loading.value = false
  }
})

function riskLabel(l) {
  return { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }[l] || l
}
function statusLabel(s) {
  return { draft: '待诊断', diagnosed: '已诊断', in_progress: '进行中', resolved: '已解决', escalated: '已升级' }[s] || s
}
function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}
function getProgress(status) {
  return { draft: 15, diagnosed: 35, in_progress: 65, resolved: 100, escalated: 80 }[status] || 0
}
</script>
<style scoped>
.page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; padding-bottom: 80px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; }
.main-content { padding: 0 20px 40px; }

.filter-tabs { display: flex; gap: 8px; margin-bottom: 16px; overflow-x: auto; padding-bottom: 4px; }
.tab { background: #fff; border: 1px solid #E0D8CE; border-radius: 20px; padding: 6px 16px; font-size: 13px; color: #6B6560; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
.tab.active { background: #E8A33D; border-color: #E8A33D; color: #fff; }

.loading-state { text-align: center; padding: 48px 0; color: #9E9893; }
.empty-state { text-align: center; padding: 48px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state p { color: #9E9893; font-size: 14px; margin-bottom: 12px; }
.btn-link { background: none; border: none; color: #E8A33D; font-size: 14px; font-weight: 600; cursor: pointer; }

.case-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #4CAF50; transition: transform 0.15s, box-shadow 0.15s; }
.case-card.clickable { cursor: pointer; }
.case-card.clickable:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.case-card.risk-yellow { border-left-color: #FFC107; }
.case-card.risk-orange { border-left-color: #FF9800; }
.case-card.risk-red { border-left-color: #F44336; }

.case-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; background: #4CAF50; flex-shrink: 0; }
.risk-dot.dot-yellow { background: #FFC107; }
.risk-dot.dot-orange { background: #FF9800; }
.risk-dot.dot-red { background: #F44336; }

.case-title { font-size: 15px; font-weight: 600; }
.case-desc { font-size: 13px; color: #6B6560; margin-bottom: 8px; line-height: 1.5; }
.case-meta { display: flex; gap: 12px; align-items: center; font-size: 12px; color: #9E9893; margin-bottom: 8px; }

.status-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.status-draft { background: #f0f0f0; color: #999; }
.status-diagnosed { background: #FFF3E0; color: #E8A33D; }
.status-in_progress { background: #E3F2FD; color: #1976D2; }
.status-resolved { background: #E8F5E9; color: #4CAF50; }
.status-escalated { background: #FBE9E7; color: #F44336; }

.risk-green { color: #4CAF50; }
.risk-yellow { color: #FFC107; }
.risk-orange { color: #FF9800; }
.risk-red { color: #F44336; }

.progress-bar { height: 3px; background: #f0f0f0; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #E8A33D, #4CAF50); border-radius: 2px; transition: width 0.3s; }
</style>
