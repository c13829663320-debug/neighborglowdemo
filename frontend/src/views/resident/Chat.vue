<template>
  <div class="page ng-fade-in">
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
.page { max-width: 480px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; background: var(--ng-bg-mobile); }

.top-bar { display: flex; align-items: center; padding: var(--ng-space-3) var(--ng-space-4); background: var(--ng-bg-card); border-bottom: 1px solid var(--ng-border); flex-shrink: 0; }
.btn-back { background: none; border: none; font-size: var(--ng-fs-body); color: var(--ng-primary-deep); cursor: pointer; margin-right: var(--ng-space-3); transition: opacity var(--ng-dur-fast) var(--ng-ease); }
.btn-back:hover { opacity: 0.75; }
.header-info { flex: 1; }
.header-info h1 { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-text-main); margin: 0; }
.member-count { font-size: var(--ng-fs-small); color: var(--ng-text-secondary); }

.chat-area { flex: 1; overflow-y: auto; padding: var(--ng-space-3) var(--ng-space-4); }
.date-divider { text-align: center; font-size: var(--ng-fs-small); color: var(--ng-text-hint); margin: var(--ng-space-4) 0 10px; }
.empty-chat { text-align: center; color: var(--ng-text-hint); padding: 60px 0; font-size: var(--ng-fs-body); }

.msg-row { display: flex; align-items: flex-start; margin-bottom: 14px; gap: var(--ng-space-2); }
.msg-row.mine { flex-direction: row-reverse; }

.avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--ng-border-strong); color: var(--ng-text-main); display: flex; align-items: center; justify-content: center; font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title); flex-shrink: 0; }
.self-avatar { background: var(--ng-primary); color: var(--ng-text-inverse); }
.ai-avatar { background: var(--ng-primary-deep); color: var(--ng-text-inverse); }

.msg-body { max-width: 72%; }
.msg-meta { display: flex; align-items: center; gap: 6px; margin-bottom: var(--ng-space-1); font-size: var(--ng-fs-small); }
.mine .msg-meta { flex-direction: row-reverse; }
.sender-name { color: var(--ng-text-secondary); }
.msg-time { color: var(--ng-text-hint); }
.ai-badge { background: var(--ng-primary-deep); color: var(--ng-text-inverse); font-size: 10px; padding: 1px 5px; border-radius: var(--ng-radius-tag); font-weight: var(--ng-fw-title); }

.bubble { padding: 10px 14px; border-radius: var(--ng-radius-btn); font-size: var(--ng-fs-body); line-height: var(--ng-lh); word-break: break-word; }
.msg-row:not(.mine) .bubble { background: var(--ng-bg-card); color: var(--ng-text-main); border: 1px solid var(--ng-border); }
.msg-row.mine .bubble { background: var(--ng-primary); color: var(--ng-text-inverse); }
.msg-row.agent .bubble { background: var(--ng-primary-soft2); border-color: var(--ng-primary-soft); }

.input-bar { display: flex; align-items: center; gap: 10px; padding: var(--ng-space-3) var(--ng-space-4); padding-bottom: calc(var(--ng-space-3) + env(safe-area-inset-bottom, 0px)); background: var(--ng-bg-card); border-top: 1px solid var(--ng-border); flex-shrink: 0; }
.msg-input { flex: 1; border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-input); padding: 10px var(--ng-space-4); font-size: var(--ng-fs-body); outline: none; background: var(--ng-bg-mobile); color: var(--ng-text-main); font-family: inherit; box-sizing: border-box; transition: border-color var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease); }
.msg-input:focus { border-color: var(--ng-primary); box-shadow: 0 0 0 3px var(--ng-primary-tint); }
.send-btn { background: var(--ng-gradient-btn); color: var(--ng-text-inverse); border: none; border-radius: var(--ng-radius-btn); padding: 10px var(--ng-space-5); font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title); cursor: pointer; box-shadow: var(--ng-shadow-btn); transition: all var(--ng-dur-fast) var(--ng-ease); }
.send-btn:disabled { background: var(--ng-border-strong); box-shadow: none; cursor: not-allowed; }
.send-btn:not(:disabled):hover { background: var(--ng-primary-dark); }
.send-btn:not(:disabled):active { transform: scale(0.98); }
</style>
