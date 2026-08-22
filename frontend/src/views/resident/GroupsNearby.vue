<template>
  <div class="page ng-fade-in">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">&larr; 返回</button>
      <h1>社区群组</h1>
      <span class="top-spacer"></span>
    </header>

    <!-- Tab Switcher -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'mine' }"
        @click="activeTab = 'mine'"
      >我的群组</button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'nearby' }"
        @click="activeTab = 'nearby'"
      >附近群组</button>
    </div>

    <main class="main-content">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <span class="spinner"></span>
        <span>加载中...</span>
      </div>

      <!-- 我的群组 -->
      <template v-if="!loading && activeTab === 'mine'">
        <div v-if="myGroups.length === 0" class="empty-state">
          <div class="empty-icon">&#x1F3E0;</div>
          <p>你还没有加入任何群组</p>
          <button class="btn-text" @click="activeTab = 'nearby'">去附近看看 &rarr;</button>
        </div>
        <div v-else class="group-list">
          <div v-for="g in myGroups" :key="g.id" class="group-card">
            <div class="group-header">
              <span class="group-name">{{ g.name }}</span>
              <span class="member-count">{{ g.member_count || 0 }} 人</span>
            </div>
            <p class="group-desc">{{ g.description || '暂无简介' }}</p>
            <div class="group-tags" v-if="g.tags && g.tags.length">
              <span v-for="tag in g.tags" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>
            <div class="group-footer">
              <button class="btn-enter" @click="enterGroup(g.id)">进入群聊 &rarr;</button>
            </div>
          </div>
        </div>
      </template>

      <!-- 附近群组 -->
      <template v-if="!loading && activeTab === 'nearby'">
        <div v-if="nearbyGroups.length === 0" class="empty-state">
          <div class="empty-icon">&#x1F50D;</div>
          <p>附近暂时没有可用的群组</p>
        </div>
        <div v-else class="group-list">
          <div v-for="g in nearbyGroups" :key="g.id" class="group-card">
            <div class="group-header">
              <span class="group-name">{{ g.name }}</span>
              <span class="group-meta-right">
                <span class="member-count">{{ g.member_count || 0 }} 人</span>
                <span class="distance">{{ g._distance }}</span>
              </span>
            </div>
            <p class="group-desc">{{ g.description || '暂无简介' }}</p>
            <div class="group-tags" v-if="g.tags && g.tags.length">
              <span v-for="tag in g.tags" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>
            <div class="group-footer">
              <button
                class="btn-join"
                :disabled="joiningId === g.id"
                @click="joinGroup(g)"
              >{{ joiningId === g.id ? '加入中...' : '加入' }}</button>
            </div>
          </div>
        </div>
      </template>
    </main>

    <!-- Create Group Section -->
    <section class="create-section">
      <button class="btn-create-toggle" @click="showCreateForm = !showCreateForm">
        {{ showCreateForm ? '收起' : '创建新群组 +' }}
      </button>
      <transition name="slide">
        <div v-if="showCreateForm" class="create-form">
          <div class="form-field">
            <label>群组名称</label>
            <input v-model="newGroup.name" type="text" placeholder="输入群组名称" maxlength="30" />
          </div>
          <div class="form-field">
            <label>群组简介</label>
            <textarea v-model="newGroup.description" placeholder="简单描述这个群组" rows="3" maxlength="200"></textarea>
          </div>
          <div class="form-field">
            <label>群组类型</label>
            <select v-model="newGroup.group_type">
              <option value="" disabled>请选择类型</option>
              <option value="neighbor">邻里互助</option>
              <option value="interest">兴趣爱好</option>
              <option value="support">支持小组</option>
            </select>
          </div>
          <button
            class="btn-submit"
            :disabled="!canCreate || creating"
            @click="createGroup"
          >{{ creating ? '创建中...' : '创建群组' }}</button>
        </div>
      </transition>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { groups as groupsApi } from '../../api'

const router = useRouter()

const activeTab = ref('mine')
const loading = ref(false)
const myGroups = ref([])
const nearbyGroups = ref([])
const joiningId = ref(null)

// Create form
const showCreateForm = ref(false)
const creating = ref(false)
const newGroup = ref({
  name: '',
  description: '',
  group_type: '',
})

const canCreate = computed(() => {
  return newGroup.value.name.trim() && newGroup.value.group_type
})

// Mock distances for nearby groups
const mockDistances = ['0.3km', '0.5km', '0.8km', '1.0km', '1.2km', '1.5km', '2.0km']
function randomDistance() {
  return mockDistances[Math.floor(Math.random() * mockDistances.length)]
}

async function fetchMyGroups() {
  try {
    const res = await groupsApi.my()
    myGroups.value = Array.isArray(res.data) ? res.data : (res.data?.items || [])
  } catch (e) {
    console.error('Failed to load my groups', e)
    myGroups.value = []
  }
}

async function fetchNearbyGroups() {
  try {
    const res = await groupsApi.list({ nearby: true })
    let list = Array.isArray(res.data) ? res.data : (res.data?.items || [])
    // Filter out groups user already joined
    const myIds = new Set(myGroups.value.map(g => g.id))
    list = list.filter(g => !myIds.has(g.id))
    // Attach mock distance
    list.forEach(g => {
      if (!g._distance) g._distance = randomDistance()
    })
    nearbyGroups.value = list
  } catch (e) {
    console.error('Failed to load nearby groups', e)
    nearbyGroups.value = []
  }
}

async function loadData() {
  loading.value = true
  await fetchMyGroups()
  await fetchNearbyGroups()
  loading.value = false
}

function enterGroup(id) {
  router.push(`/resident/groups/${id}`)
}

async function joinGroup(group) {
  joiningId.value = group.id
  try {
    await groupsApi.join(group.id)
    // Move from nearby to my groups
    nearbyGroups.value = nearbyGroups.value.filter(g => g.id !== group.id)
    myGroups.value.push(group)
  } catch (e) {
    console.error('Failed to join group', e)
  } finally {
    joiningId.value = null
  }
}

async function createGroup() {
  if (!canCreate.value) return
  creating.value = true
  try {
    const res = await groupsApi.create({
      name: newGroup.value.name.trim(),
      description: newGroup.value.description.trim(),
      group_type: newGroup.value.group_type,
    })
    const created = res.data
    myGroups.value.unshift(created)
    // Reset form
    newGroup.value = { name: '', description: '', group_type: '' }
    showCreateForm.value = false
    activeTab.value = 'mine'
  } catch (e) {
    console.error('Failed to create group', e)
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--ng-bg-mobile);
}

/* Header */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
}
.btn-back {
  background: none;
  border: none;
  font-size: var(--ng-fs-body);
  color: var(--ng-primary-deep);
  cursor: pointer;
  min-width: 60px;
  transition: opacity var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { opacity: 0.75; }
.top-bar h1 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
}
.top-spacer {
  min-width: 60px;
}

/* Tabs */
.tab-bar {
  display: flex;
  margin: 0 var(--ng-page-margin-mobile) var(--ng-space-4);
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-1);
  box-shadow: var(--ng-shadow-card);
}
.tab-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 0;
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-secondary);
  border-radius: var(--ng-radius-tag);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.tab-btn.active {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  font-weight: var(--ng-fw-title);
  box-shadow: var(--ng-shadow-btn);
}

/* Main Content */
.main-content {
  padding: 0 var(--ng-page-margin-mobile) var(--ng-space-5);
  min-height: 300px;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--ng-space-2);
  padding: 60px 0;
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
}
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 48px var(--ng-space-5);
  color: var(--ng-text-hint);
}
.empty-icon {
  font-size: 48px;
  margin-bottom: var(--ng-space-3);
  opacity: 0.6;
}
.empty-state p {
  font-size: var(--ng-fs-body);
  margin-bottom: var(--ng-space-4);
}
.btn-text {
  background: none;
  border: none;
  color: var(--ng-primary-deep);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  transition: opacity var(--ng-dur-fast) var(--ng-ease);
}
.btn-text:hover { opacity: 0.75; }

/* Group List */
.group-list {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}

/* Group Card */
.group-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding);
  box-shadow: var(--ng-shadow-card);
  border: 1px solid var(--ng-border);
  transition: transform var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
}
.group-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--ng-shadow-card-hover);
}
.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--ng-space-2);
}
.group-name {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
}
.group-meta-right {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
}
.member-count {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}
.distance {
  font-size: var(--ng-fs-small);
  color: var(--ng-primary-deep);
  background: var(--ng-primary-tint);
  padding: 2px var(--ng-space-2);
  border-radius: var(--ng-radius-tag);
}
.group-desc {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: var(--ng-space-3);
}
.tag-chip {
  font-size: var(--ng-fs-small);
  color: var(--ng-primary-deep);
  background: var(--ng-primary-soft);
  border: 1px solid var(--ng-primary-tint);
  padding: 3px 10px;
  border-radius: var(--ng-radius-tag);
}
.group-footer {
  display: flex;
  justify-content: flex-end;
}
.btn-enter {
  background: none;
  border: 1.5px solid var(--ng-primary);
  color: var(--ng-primary-deep);
  padding: 7px 18px;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-enter:hover {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
}
.btn-enter:active { transform: scale(0.98); }
.btn-join {
  background: var(--ng-gradient-btn);
  border: none;
  color: var(--ng-text-inverse);
  padding: var(--ng-space-2) var(--ng-space-6);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-join:hover { background: var(--ng-primary-dark); }
.btn-join:active { transform: scale(0.98); }
.btn-join:disabled {
  background: var(--ng-border-strong);
  box-shadow: none;
  cursor: not-allowed;
}

/* Create Section */
.create-section {
  padding: 0 var(--ng-page-margin-mobile) 40px;
}
.btn-create-toggle {
  width: 100%;
  background: var(--ng-bg-card);
  border: 1.5px dashed var(--ng-border-strong);
  color: var(--ng-primary-deep);
  padding: 14px;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-create-toggle:hover {
  border-color: var(--ng-primary);
  background: var(--ng-bg-mobile);
}

/* Create Form */
.create-form {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-5);
  margin-top: var(--ng-space-3);
  box-shadow: var(--ng-shadow-card);
  border: 1px solid var(--ng-border);
}
.form-field {
  margin-bottom: var(--ng-space-4);
}
.form-field label {
  display: block;
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
  margin-bottom: 6px;
}
.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  padding: 10px 14px;
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  background: var(--ng-bg-card);
  outline: none;
  transition: border-color var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
  font-family: inherit;
  box-sizing: border-box;
}
.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  border-color: var(--ng-primary);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}
.form-field textarea {
  resize: vertical;
}
.btn-submit {
  width: 100%;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  padding: 13px;
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-submit:hover { background: var(--ng-primary-dark); }
.btn-submit:active { transform: scale(0.98); }
.btn-submit:disabled {
  background: var(--ng-border-strong);
  box-shadow: none;
  cursor: not-allowed;
}

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all var(--ng-dur-base) var(--ng-ease);
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 400px;
  transform: translateY(0);
}
</style>
