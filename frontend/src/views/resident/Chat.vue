<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">&larr; 返回</button>
      <div class="header-info">
        <h1>{{ topicName || groupName || '群聊' }}</h1>
        <span class="member-count" v-if="memberCount">{{ memberCount }} 人</span>
      </div>
      <span></span>
    </header>

    <div class="chat-area" ref="chatArea">
      <template v-for="(group, idx) in groupedMessages" :key="idx">
        <div class="date-divider">{{ group.date }}</div>
        <div
          v-for="msg in group.items"
          :key="msg.id"
          class="msg-row"
          :class="{ mine: msg.is_self, agent: msg.is_agent }"
        >
          <div v-if="!msg.is_self" class="avatar" :class="{ 'ai-avatar': msg.is_agent }">
            {{ (msg.sender_name || '?')[0] }}
          </div>
          <div class="msg-body">
            <div class="msg-meta">
              <span class="sender-name">{{ msg.sender_name }}</span>
              <span v-if="msg.is_agent" class="ai-badge">AI</span>
              <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <div class="bubble">{{ msg.content }}</div>
          </div>
          <div v-if="msg.is_self" class="avatar self-avatar">{{ (msg.sender_name || '我')[0] }}</div>
        </div>
      </template>
      <div v-if="messages.length === 0 && !loading" class="empty-chat">暂无消息，来说点什么吧</div>
    </div>

    <div class="input-bar">
      <input
        v-model="inputText"
        @keyup.enter="send"
        placeholder="输入消息..."
        class="msg-input"
      />
      <button @click="send" class="send-btn" :disabled="!inputText.trim()">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { groups as groupsApi } from '../../api'

const route = useRoute()
const groupId = route.params.id
const topicId = computed(() => route.query.topic || null)

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const chatArea = ref(null)
const groupName = ref('')
const topicName = ref('')
const memberCount = ref(0)
let pollTimer = null

const groupedMessages = computed(() => {
  const groups = []
  let lastDate = ''
  for (const msg of messages.value) {
    const d = new Date(msg.created_at)
    const dateStr = `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
    if (dateStr !== lastDate) {
      groups.push({ date: dateStr, items: [] })
      lastDate = dateStr
    }
    groups[groups.length - 1].items.push(msg)
  }
  return groups
})

function formatTime(ts) {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function fetchMessages() {
  try {
    const params = { topic_id: topicId.value, limit: 50, offset: 0 }
    const res = await groupsApi.chatHistory(groupId, params)
    const data = res.data || res
    messages.value = Array.isArray(data) ? data : (data.messages || [])
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('加载消息失败', e)
  }
}

async function fetchGroupInfo() {
  try {
    const res = await groupsApi.get(groupId)
    const g = res.data || res
    groupName.value = g.name || ''
    memberCount.value = g.member_count || 0
    if (topicId.value && g.topics) {
      const t = g.topics.find(t => String(t.id) === String(topicId.value))
      if (t) topicName.value = t.name
    }
  } catch (e) { /* ignore */ }
}

function scrollToBottom() {
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}

async function send() {
  const content = inputText.value.trim()
  if (!content) return
  inputText.value = ''
  try {
    await groupsApi.sendMessage(groupId, { content, topic_id: topicId.value })
    await fetchMessages()
  } catch (e) {
    alert('发送失败，请重试')
  }
}

onMounted(() => {
  fetchGroupInfo()
  fetchMessages()
  pollTimer = setInterval(fetchMessages, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

watch(topicId, () => {
  messages.value = []
  fetchMessages()
})
</script>

<style scoped>
.page { max-width: 480px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; background: #FFF9F0; }

.top-bar { display: flex; align-items: center; padding: 12px 16px; background: #fff; border-bottom: 1px solid #E0D8CE; flex-shrink: 0; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; margin-right: 12px; }
.header-info { flex: 1; }
.header-info h1 { font-size: 16px; font-weight: 600; color: #2D2A26; margin: 0; }
.member-count { font-size: 12px; color: #6B6560; }

.chat-area { flex: 1; overflow-y: auto; padding: 12px 16px; }
.date-divider { text-align: center; font-size: 12px; color: #6B6560; margin: 16px 0 10px; }
.empty-chat { text-align: center; color: #6B6560; padding: 60px 0; font-size: 14px; }

.msg-row { display: flex; align-items: flex-start; margin-bottom: 14px; gap: 8px; }
.msg-row.mine { flex-direction: row-reverse; }

.avatar { width: 36px; height: 36px; border-radius: 50%; background: #E0D8CE; color: #2D2A26; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600; flex-shrink: 0; }
.self-avatar { background: #E8A33D; color: #fff; }
.ai-avatar { background: #5B8DEF; color: #fff; }

.msg-body { max-width: 72%; }
.msg-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; font-size: 12px; }
.mine .msg-meta { flex-direction: row-reverse; }
.sender-name { color: #6B6560; }
.msg-time { color: #6B6560; }
.ai-badge { background: #5B8DEF; color: #fff; font-size: 10px; padding: 1px 5px; border-radius: 4px; font-weight: 600; }

.bubble { padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.6; word-break: break-word; }
.msg-row:not(.mine) .bubble { background: #fff; color: #2D2A26; border: 1px solid #E0D8CE; border-top-left-radius: 4px; }
.msg-row.mine .bubble { background: #E8A33D; color: #fff; border-top-right-radius: 4px; }
.msg-row.agent .bubble { background: #F0F4FF; border-color: #C8D6F0; }

.input-bar { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: #fff; border-top: 1px solid #E0D8CE; flex-shrink: 0; }
.msg-input { flex: 1; border: 1px solid #E0D8CE; border-radius: 22px; padding: 10px 16px; font-size: 15px; outline: none; background: #FFF9F0; color: #2D2A26; }
.msg-input:focus { border-color: #E8A33D; }
.send-btn { background: #E8A33D; color: #fff; border: none; border-radius: 22px; padding: 10px 20px; font-size: 15px; font-weight: 600; cursor: pointer; }
.send-btn:disabled { opacity: 0.5; cursor: default; }
.send-btn:not(:disabled):active { opacity: 0.85; }
</style>
