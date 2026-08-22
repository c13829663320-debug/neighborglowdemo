<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">&larr; 返回</button>
      <h1>{{ group.name || '群组详情' }}</h1>
      <span></span>
    </header>

    <main class="main-content" v-if="group">
      <!-- Group Info Card -->
      <section class="info-card">
        <h2 class="group-name">{{ group.name }}</h2>
        <p class="group-desc">{{ group.description || '暂无简介' }}</p>
        <div class="meta-row">
          <span class="meta-item">&#x1F465; {{ members.length }} 位成员</span>
        </div>
        <div class="tags" v-if="group.tags && group.tags.length">
          <span v-for="tag in group.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </section>

      <!-- Topics -->
      <section class="section">
        <h3 class="section-title">话题</h3>
        <div v-if="topics.length === 0" class="empty-hint">暂无话题</div>
        <div
          v-for="topic in topics"
          :key="topic.id"
          class="topic-card"
          @click="goChat(topic)"
        >
          <div class="topic-name">{{ topic.name }}</div>
          <div class="topic-meta">{{ topic.message_count || 0 }} 条消息</div>
          <span class="arrow">&rarr;</span>
        </div>
      </section>

      <!-- Members (collapsible) -->
      <section class="section">
        <div class="section-header" @click="membersExpanded = !membersExpanded">
          <h3 class="section-title">成员 ({{ members.length }})</h3>
          <span class="toggle">{{ membersExpanded ? '收起' : '展开' }}</span>
        </div>
        <div v-if="membersExpanded" class="members-grid">
          <div v-for="m in members" :key="m.id" class="member-item">
            <div class="avatar">{{ (m.name || m.nickname || '?')[0] }}</div>
            <span class="member-name">{{ m.name || m.nickname }}</span>
          </div>
        </div>
      </section>

      <!-- Actions -->
      <div class="actions">
        <button class="btn-primary" @click="enterChat">进入聊天 &rarr;</button>
        <button class="btn-danger" @click="handleLeave">退出群组</button>
      </div>
    </main>

    <div v-else class="loading">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { groups as groupsApi } from '../../api'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const group = ref(null)
const members = ref([])
const topics = ref([])
const membersExpanded = ref(false)

onMounted(async () => {
  try {
    const [gRes, mRes, tRes] = await Promise.all([
      groupsApi.get(id),
      groupsApi.members(id),
      groupsApi.topics(id),
    ])
    group.value = gRes.data || gRes
    members.value = mRes.data || mRes || []
    topics.value = tRes.data || tRes || []
  } catch (e) {
    console.error('加载群组详情失败', e)
  }
})

function goChat(topic) {
  router.push(`/resident/groups/${id}/chat?topic=${topic.id}`)
}

function enterChat() {
  router.push(`/resident/groups/${id}/chat`)
}

async function handleLeave() {
  if (!confirm('确定要退出该群组吗？')) return
  try {
    await groupsApi.leave(id)
    router.back()
  } catch (e) {
    alert('退出失败，请重试')
  }
}
</script>

<style scoped>
.page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; position: sticky; top: 0; background: #FFF9F0; z-index: 10; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; color: #2D2A26; }
.main-content { padding: 0 20px 32px; }
.loading { text-align: center; padding: 60px 0; color: #6B6560; }

.info-card { background: #fff; border-radius: 14px; padding: 20px; border: 1px solid #E0D8CE; margin-bottom: 20px; }
.group-name { font-size: 20px; font-weight: 700; color: #2D2A26; margin-bottom: 8px; }
.group-desc { font-size: 14px; color: #6B6560; line-height: 1.6; margin-bottom: 12px; }
.meta-row { font-size: 13px; color: #6B6560; margin-bottom: 10px; }
.meta-item { margin-right: 16px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { background: #FFF3E0; color: #E8A33D; font-size: 12px; padding: 3px 10px; border-radius: 20px; }

.section { margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.section-title { font-size: 16px; font-weight: 600; color: #2D2A26; margin-bottom: 12px; }
.toggle { font-size: 13px; color: #E8A33D; }
.empty-hint { font-size: 14px; color: #6B6560; padding: 16px 0; }

.topic-card { background: #fff; border: 1px solid #E0D8CE; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; display: flex; align-items: center; cursor: pointer; position: relative; }
.topic-card:active { background: #FFF3E0; }
.topic-name { font-size: 15px; font-weight: 500; color: #2D2A26; flex: 1; }
.topic-meta { font-size: 12px; color: #6B6560; margin-right: 12px; }
.arrow { color: #E8A33D; font-size: 16px; }

.members-grid { display: flex; flex-wrap: wrap; gap: 16px; }
.member-item { display: flex; flex-direction: column; align-items: center; width: 56px; }
.avatar { width: 44px; height: 44px; border-radius: 50%; background: #E8A33D; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.member-name { font-size: 11px; color: #6B6560; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 56px; }

.actions { display: flex; flex-direction: column; gap: 12px; margin-top: 24px; }
.btn-primary { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 14px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-primary:active { opacity: 0.85; }
.btn-danger { background: #fff; color: #D9534F; border: 1px solid #D9534F; border-radius: 12px; padding: 14px; font-size: 15px; cursor: pointer; }
.btn-danger:active { background: #FFF0F0; }
</style>
