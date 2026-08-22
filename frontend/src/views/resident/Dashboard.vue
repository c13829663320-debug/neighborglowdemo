<template>
  <div class="resident-dashboard">
    <header class="top-bar">
      <h1>🌟 邻光</h1>
      <div class="user-info">
        <span>{{ userInfo?.username || '用户' }}</span>
        <button @click="logout" class="btn-logout">退出</button>
      </div>
    </header>
    <main class="main-content">
      <section class="hero">
        <h2>邻里之间，有些话只是需要换一种方式说。</h2>
        <p>描述你遇到的问题，邻光会帮你理清情况、找到合适的表达，并陪你练习下一次沟通。</p>
        <button @click="$router.push('/resident/submit')" class="btn-primary">开始梳理问题</button>
      </section>
      <section class="quick-scenarios">
        <h3>快捷场景</h3>
        <div class="scenario-grid">
          <div v-for="s in scenarios" :key="s.key" class="scenario-card" @click="selectScenario(s)">
            <span class="scenario-icon">{{ s.icon }}</span>
            <span class="scenario-label">{{ s.label }}</span>
          </div>
        </div>
      </section>
      <section class="my-cases">
        <h3>我的案例</h3>
        <div v-if="cases.length === 0" class="empty-state">
          <p>还没有案例，从描述你遇到的问题开始</p>
        </div>
        <div v-else class="case-list">
          <div v-for="c in cases" :key="c.id" class="case-card" :class="'risk-' + c.risk_level">
            <div class="case-header">
              <span class="risk-badge" :class="'risk-' + c.risk_level"></span>
              <span class="case-title">{{ c.title }}</span>
            </div>
            <p class="case-desc">{{ c.description?.slice(0, 60) }}...</p>
            <div class="case-meta">
              <span class="case-status">{{ c.status }}</span>
              <span class="case-date">{{ new Date(c.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'
const router = useRouter()
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))
const cases = ref([])
const scenarios = [
  { key: 'noise', icon: '🔊', label: '深夜噪音' },
  { key: 'leak', icon: '💧', label: '漏水纠纷' },
  { key: 'public_space', icon: '🏢', label: '公共区域' },
  { key: 'pet', icon: '🐕', label: '宠物问题' },
  { key: 'garbage', icon: '🗑️', label: '异味困扰' },
  { key: 'renovation', icon: '🔨', label: '装修施工' },
]
onMounted(async () => {
  try {
    const res = await casesApi.list()
    cases.value = res.data
  } catch (e) {
    console.error('Failed to load cases', e)
  }
})
function selectScenario(s) {
  router.push({ path: '/resident/submit', query: { scenario: s.key } })
}
function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  router.push('/login')
}
</script>
<style scoped>
.resident-dashboard { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.top-bar h1 { font-size: 20px; color: #E8A33D; }
.user-info { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #6B6560; }
.btn-logout { background: none; border: 1px solid #E0D8CE; border-radius: 8px; padding: 4px 12px; font-size: 13px; color: #6B6560; cursor: pointer; }
.main-content { padding: 0 20px 40px; }
.hero { background: linear-gradient(135deg, #FDE8C8, #FFF3E0); border-radius: 16px; padding: 24px; margin-bottom: 24px; }
.hero h2 { font-size: 20px; font-weight: 600; color: #2D2A26; margin-bottom: 12px; line-height: 1.4; }
.hero p { font-size: 14px; color: #6B6560; margin-bottom: 20px; line-height: 1.6; }
.btn-primary { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 14px 32px; font-size: 16px; font-weight: 600; cursor: pointer; width: 100%; }
.btn-primary:hover { background: #D4922E; }
.quick-scenarios { margin-bottom: 24px; }
.quick-scenarios h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.scenario-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.scenario-card { background: #fff; border-radius: 12px; padding: 16px 8px; text-align: center; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.04); transition: transform 0.2s; }
.scenario-card:hover { transform: translateY(-2px); }
.scenario-icon { font-size: 24px; display: block; margin-bottom: 6px; }
.scenario-label { font-size: 13px; color: #2D2A26; }
.my-cases h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.empty-state { text-align: center; padding: 32px; color: #9E9893; font-size: 14px; }
.case-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-left: 4px solid #4CAF50; }
.case-card.risk-yellow { border-left-color: #FFC107; }
.case-card.risk-orange { border-left-color: #FF9800; }
.case-card.risk-red { border-left-color: #F44336; }
.case-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.case-title { font-size: 15px; font-weight: 600; }
.case-desc { font-size: 13px; color: #6B6560; margin-bottom: 8px; }
.case-meta { display: flex; justify-content: space-between; font-size: 12px; color: #9E9893; }
</style>
