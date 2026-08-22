<template>
  <div class="resident-dashboard">
    <header class="top-bar">
      <h1>🌟 邻光</h1>
      <div class="user-info">
        <span class="user-name" @click="router.push('/resident/profile')">{{ userInfo?.display_name || userInfo?.username || '用户' }}</span>
        <div class="avatar" @click="router.push('/resident/profile')">{{ avatarLetter }}</div>
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
        <div class="section-header">
          <h3>我的案例</h3>
          <a class="link-more" @click.prevent="router.push('/resident/my-requests')">查看全部</a>
        </div>
        <div v-if="cases.length === 0" class="empty-state">
          <div class="empty-icon">🌱</div>
          <p class="empty-title">第一次使用？</p>
          <p class="empty-text">从描述你遇到的问题开始，<br />邻光会帮你理清情况，一起想办法怎么开口。</p>
          <button class="btn-primary empty-btn" @click="router.push('/resident/submit')">开始描述问题</button>
          <p class="empty-tip">也可以点击上方常见场景快速开始</p>
        </div>
        <div v-else class="case-list">
          <div v-for="c in cases.slice(0, 3)" :key="c.id" class="case-card clickable" :class="'risk-' + c.risk_level" @click="router.push('/resident/case/' + c.id)">
            <div class="case-header">
              <span class="risk-badge" :class="'risk-' + c.risk_level"></span>
              <span class="case-title">{{ c.title }}</span>
            </div>
            <p class="case-desc">{{ c.description?.slice(0, 60) }}...</p>
            <div class="case-meta">
              <span class="case-status">{{ statusLabel(c.status) }}</span>
              <span class="case-date">{{ new Date(c.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Bottom Navigation -->
    <nav class="bottom-nav">
      <a class="nav-item active" @click.prevent="router.push('/resident')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>首页</span>
      </a>
      <a class="nav-item" @click.prevent="router.push('/resident/my-requests')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <span>案例</span>
      </a>
      <a class="nav-item" @click.prevent="router.push('/resident/groups')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        <span>群组</span>
      </a>
      <a class="nav-item" @click.prevent="router.push('/resident/profile')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <span>我的</span>
      </a>
    </nav>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
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

const avatarLetter = computed(() => {
  const name = userInfo.value?.display_name || userInfo.value?.username || '?'
  return name.charAt(0).toUpperCase()
})

function statusLabel(s) {
  const map = { pending: '待处理', diagnosed: '已诊断', mediating: '调解中', escalated: '已升级', resolved: '已解决', closed: '已关闭' }
  return map[s] || s || ''
}

onMounted(async () => {
  try {
    const res = await casesApi.list()
    cases.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.error('Failed to load cases', e)
  }
})
function selectScenario(s) {
  router.push({ path: '/resident/submit', query: { scenario: s.key } })
}
</script>
<style scoped>
.resident-dashboard { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif; color: #2D2A26; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #fff; border-bottom: 1px solid #E0D8CE; position: sticky; top: 0; z-index: 10; }
.top-bar h1 { font-size: 20px; color: #E8A33D; margin: 0; }
.user-info { display: flex; align-items: center; gap: 10px; }
.user-name { font-size: 14px; color: #2D2A26; font-weight: 500; cursor: pointer; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: #E8A33D; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; cursor: pointer; transition: transform 0.2s; }
.avatar:hover { transform: scale(1.1); }
.main-content { padding: 0 20px 100px; }
.hero { background: linear-gradient(135deg, #FDE8C8, #FFF3E0); border-radius: 16px; padding: 24px; margin: 16px 0 24px; }
.hero h2 { font-size: 20px; font-weight: 600; color: #2D2A26; margin-bottom: 12px; line-height: 1.4; }
.hero p { font-size: 14px; color: #6B6560; margin-bottom: 20px; line-height: 1.6; }
.btn-primary { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 14px 32px; font-size: 16px; font-weight: 600; cursor: pointer; width: 100%; transition: background 0.2s; }
.btn-primary:hover { background: #D4922E; }
.quick-scenarios { margin-bottom: 24px; }
.quick-scenarios h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.scenario-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.scenario-card { background: #fff; border-radius: 12px; padding: 16px 8px; text-align: center; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.04); transition: transform 0.2s; border: 1px solid #E0D8CE; }
.scenario-card:hover { transform: translateY(-2px); border-color: #E8A33D; }
.scenario-icon { font-size: 24px; display: block; margin-bottom: 6px; }
.scenario-label { font-size: 13px; color: #2D2A26; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h3 { font-size: 16px; font-weight: 600; margin: 0; }
.link-more { font-size: 13px; color: #E8A33D; cursor: pointer; text-decoration: none; }
.link-more:hover { text-decoration: underline; }
.my-cases { margin-bottom: 24px; }
.empty-state { text-align: center; padding: 36px 24px; color: #9E9893; font-size: 14px; background: #fff; border-radius: 16px; border: 1px dashed #E0C9A6; animation: ng-fade-in 0.35s ease; }
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-title { font-size: 17px; font-weight: 600; color: #2D2A26; margin: 0 0 8px; }
.empty-text { font-size: 14px; color: #6B6560; line-height: 1.7; margin: 0 0 20px; }
.empty-btn { max-width: 260px; margin: 0 auto; }
.empty-tip { font-size: 12px; color: #9E9893; margin: 14px 0 0; }
.case-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-left: 4px solid #34C759; transition: transform 0.15s, box-shadow 0.15s; border: 1px solid #E0D8CE; border-left: 4px solid #34C759; }
.case-card.clickable { cursor: pointer; }
.case-card.clickable:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(232,163,61,0.12); }
.case-card.risk-yellow { border-left-color: #FF9500; }
.case-card.risk-orange { border-left-color: #FF6B35; }
.case-card.risk-red { border-left-color: #FF3B30; }
.case-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.case-title { font-size: 15px; font-weight: 600; }
.case-desc { font-size: 13px; color: #6B6560; margin-bottom: 8px; line-height: 1.5; }
.case-meta { display: flex; justify-content: space-between; font-size: 12px; color: #9E9893; }

/* Bottom Navigation */
.bottom-nav {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 100%; max-width: 480px; background: #fff; border-top: 1px solid #E0D8CE;
  display: flex; justify-content: space-around; align-items: center;
  padding: 8px 0 env(safe-area-inset-bottom, 8px); z-index: 50;
  box-shadow: 0 -2px 12px rgba(0,0,0,0.06);
}
.nav-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 4px 12px; cursor: pointer; color: #B8AFA3; text-decoration: none;
  transition: color 0.2s;
}
.nav-item:hover { color: #E8A33D; }
.nav-item.active { color: #E8A33D; }
.nav-item span { font-size: 11px; font-weight: 500; }
</style>
