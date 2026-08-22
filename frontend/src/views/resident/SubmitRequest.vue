<template>
  <div class="submit-page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">← 返回</button>
      <h1>描述问题</h1>
      <span></span>
    </header>
    <main class="main-content">
      <div class="chat-area">
        <div v-for="(msg, i) in messages" :key="i" :class="['chat-bubble', msg.role]">
          {{ msg.text }}
        </div>
        <div v-if="loading" class="chat-bubble ai">
          <span class="typing">正在理解你的情况...</span>
        </div>
      </div>
      <div class="input-area">
        <textarea v-model="input" placeholder="描述你遇到的邻里问题..." rows="3" @keydown.enter.ctrl="submit"></textarea>
        <button @click="submit" :disabled="!input.trim() || loading" class="btn-send">发送</button>
      </div>
      <div v-if="createdCase" class="result-card">
        <h3>问题已记录</h3>
        <p>风险等级：<span :class="'risk-' + createdCase.risk_level">{{ riskLabel(createdCase.risk_level) }}</span></p>
        <button @click="$router.push('/resident')" class="btn-primary">返回首页</button>
      </div>
    </main>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { cases } from '../../api'
const route = useRoute()
const input = ref('')
const messages = ref([])
const loading = ref(false)
const createdCase = ref(null)
const scenarioLabels = { noise: '深夜噪音', leak: '漏水纠纷', public_space: '公共区域', pet: '宠物问题', garbage: '异味困扰', renovation: '装修施工' }
onMounted(() => {
  messages.value.push({ role: 'ai', text: '你好，我是邻光。请描述你遇到的邻里问题，我会帮你分析情况。' })
  const scenario = route.query.scenario
  if (scenario && scenarioLabels[scenario]) {
    messages.value.push({ role: 'ai', text: `你选择了「${scenarioLabels[scenario]}」场景，请详细描述一下发生了什么？比如时间、频率、对你的影响等。` })
  }
})
async function submit() {
  if (!input.value.trim() || loading.value) return
  const text = input.value.trim()
  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  try {
    const res = await cases.create({ title: text.slice(0, 30), description: text, category: route.query.scenario || null })
    createdCase.value = res.data
    messages.value.push({ role: 'ai', text: `已为你完成初步分析。风险等级：${riskLabel(res.data.risk_level)}。你可以返回首页查看案例详情。` })
  } catch (e) {
    messages.value.push({ role: 'ai', text: '抱歉，提交时遇到了问题，请稍后重试。' })
  } finally {
    loading.value = false
  }
}
function riskLabel(level) {
  return { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }[level] || level
}
</script>
<style scoped>
.submit-page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; display: flex; flex-direction: column; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; }
.main-content { flex: 1; display: flex; flex-direction: column; padding: 0 20px 20px; }
.chat-area { flex: 1; overflow-y: auto; padding-bottom: 16px; }
.chat-bubble { max-width: 85%; padding: 12px 16px; border-radius: 16px; margin-bottom: 12px; font-size: 14px; line-height: 1.6; }
.chat-bubble.ai { background: #fff; color: #2D2A26; border-bottom-left-radius: 4px; }
.chat-bubble.user { background: #E8A33D; color: #fff; margin-left: auto; border-bottom-right-radius: 4px; }
.typing { color: #9E9893; }
.input-area { display: flex; gap: 8px; align-items: flex-end; }
.input-area textarea { flex: 1; padding: 12px 16px; border: 1px solid #E0D8CE; border-radius: 12px; font-size: 14px; resize: none; outline: none; font-family: inherit; }
.input-area textarea:focus { border-color: #E8A33D; }
.btn-send { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 12px 20px; font-size: 14px; font-weight: 600; cursor: pointer; }
.btn-send:disabled { background: #ccc; cursor: not-allowed; }
.result-card { background: #fff; border-radius: 16px; padding: 20px; margin-top: 16px; text-align: center; }
.result-card h3 { font-size: 16px; margin-bottom: 8px; }
.risk-green { color: #4CAF50; font-weight: 600; }
.risk-yellow { color: #FFC107; font-weight: 600; }
.risk-orange { color: #FF9800; font-weight: 600; }
.risk-red { color: #F44336; font-weight: 600; }
.btn-primary { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 12px 24px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 12px; width: 100%; }
</style>
