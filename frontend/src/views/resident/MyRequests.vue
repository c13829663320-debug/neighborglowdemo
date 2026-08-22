<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">← 返回</button>
      <h1>我的案例</h1>
      <span></span>
    </header>
    <main class="main-content">
      <div v-if="cases.length === 0" class="empty-state">
        <p>暂无案例记录</p>
      </div>
      <div v-else>
        <div v-for="c in cases" :key="c.id" class="case-card" :class="'risk-' + c.risk_level">
          <div class="case-title">{{ c.title }}</div>
          <p class="case-desc">{{ c.description?.slice(0, 80) }}</p>
          <div class="case-meta">
            <span :class="'risk-' + c.risk_level">{{ riskLabel(c.risk_level) }}</span>
            <span>{{ c.status }}</span>
            <span>{{ new Date(c.created_at).toLocaleDateString() }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { cases } from '../../api'
const casesList = ref([])
onMounted(async () => {
  try { const res = await cases.list(); casesList.value = res.data } catch (e) {}
})
function riskLabel(l) { return { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }[l] || l }
</script>
<style scoped>
.page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; }
.main-content { padding: 0 20px 40px; }
.empty-state { text-align: center; padding: 48px 0; color: #9E9893; }
.case-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #4CAF50; }
.case-card.risk-yellow { border-left-color: #FFC107; }
.case-card.risk-orange { border-left-color: #FF9800; }
.case-card.risk-red { border-left-color: #F44336; }
.case-title { font-size: 15px; font-weight: 600; margin-bottom: 6px; }
.case-desc { font-size: 13px; color: #6B6560; margin-bottom: 8px; }
.case-meta { display: flex; gap: 16px; font-size: 12px; color: #9E9893; }
.risk-green { color: #4CAF50; }
.risk-yellow { color: #FFC107; }
.risk-orange { color: #FF9800; }
.risk-red { color: #F44336; }
</style>
