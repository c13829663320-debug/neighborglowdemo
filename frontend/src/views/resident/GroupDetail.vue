<template>
  <div class="page ng-fade-in">
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
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--ng-bg-mobile);
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  position: sticky;
  top: 0;
  background: var(--ng-bg-mobile);
  z-index: 10;
}
.btn-back {
  background: none;
  border: none;
  font-size: var(--ng-fs-body);
  color: var(--ng-primary-deep);
  cursor: pointer;
  transition: opacity var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { opacity: 0.75; }
.top-bar h1 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.main-content { padding: 0 var(--ng-page-margin-mobile) var(--ng-space-8); }
.loading {
  text-align: center;
  padding: 60px 0;
  color: var(--ng-text-secondary);
}

.info-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-5);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
  margin-bottom: var(--ng-space-5);
}
.group-name {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-2);
}
.group-desc {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin: 0 0 var(--ng-space-3);
}
.meta-row {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin-bottom: 10px;
}
.meta-item { margin-right: var(--ng-space-4); }
.tags { display: flex; flex-wrap: wrap; gap: var(--ng-space-2); }
.tag {
  background: var(--ng-primary-soft);
  color: var(--ng-primary-deep);
  font-size: var(--ng-fs-small);
  padding: 3px 10px;
  border-radius: var(--ng-radius-tag);
}

.section { margin-bottom: var(--ng-space-5); }
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}
.section-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-3);
}
.toggle {
  font-size: var(--ng-fs-aux);
  color: var(--ng-primary-deep);
}
.empty-hint {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-hint);
  padding: var(--ng-space-4) 0;
}

.topic-card {
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-btn);
  padding: 14px var(--ng-space-4);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  cursor: pointer;
  position: relative;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.topic-card:hover { box-shadow: var(--ng-shadow-card); }
.topic-card:active { background: var(--ng-primary-soft2); }
.topic-name {
  font-size: 15px;
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
  flex: 1;
}
.topic-meta {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  margin-right: var(--ng-space-3);
}
.arrow { color: var(--ng-primary-deep); font-size: var(--ng-fs-card); }

.members-grid { display: flex; flex-wrap: wrap; gap: var(--ng-space-4); }
.member-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 56px;
}
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  margin-bottom: var(--ng-space-1);
}
.member-name {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 56px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-3);
  margin-top: var(--ng-space-6);
}
.btn-primary {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  padding: 14px;
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-primary:hover { filter: brightness(0.96); }
.btn-primary:active { transform: scale(0.98); }
.btn-danger {
  background: var(--ng-bg-card);
  color: var(--ng-risk-red);
  border: 1px solid var(--ng-risk-red);
  border-radius: var(--ng-radius-btn);
  padding: 14px;
  font-size: 15px;
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-danger:hover { background: var(--ng-risk-red-soft); }
.btn-danger:active { background: var(--ng-risk-red-soft); }
</style>
