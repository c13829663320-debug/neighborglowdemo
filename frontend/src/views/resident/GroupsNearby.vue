<template>
  <div class="page">
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
  background: #FFF9F0;
}

/* Header */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
}
.btn-back {
  background: none;
  border: none;
  font-size: 14px;
  color: #E8A33D;
  cursor: pointer;
  min-width: 60px;
}
.top-bar h1 {
  font-size: 17px;
  font-weight: 600;
  color: #2D2A26;
}
.top-spacer {
  min-width: 60px;
}

/* Tabs */
.tab-bar {
  display: flex;
  margin: 0 20px 16px;
  background: #fff;
  border-radius: 12px;
  padding: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.tab-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  color: #6B6560;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
}
.tab-btn.active {
  background: #E8A33D;
  color: #fff;
  font-weight: 600;
}

/* Main Content */
.main-content {
  padding: 0 20px 20px;
  min-height: 300px;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 60px 0;
  color: #6B6560;
  font-size: 14px;
}
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: #9E9893;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.6;
}
.empty-state p {
  font-size: 14px;
  margin-bottom: 16px;
}
.btn-text {
  background: none;
  border: none;
  color: #E8A33D;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

/* Group List */
.group-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Group Card */
.group-card {
  background: #fff;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #E0D8CE;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.group-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.07);
}
.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.group-name {
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
}
.group-meta-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.member-count {
  font-size: 12px;
  color: #9E9893;
}
.distance {
  font-size: 11px;
  color: #E8A33D;
  background: rgba(232, 163, 61, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
}
.group-desc {
  font-size: 13px;
  color: #6B6560;
  line-height: 1.5;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.tag-chip {
  font-size: 11px;
  color: #E8A33D;
  background: rgba(232, 163, 61, 0.08);
  border: 1px solid rgba(232, 163, 61, 0.2);
  padding: 3px 10px;
  border-radius: 20px;
}
.group-footer {
  display: flex;
  justify-content: flex-end;
}
.btn-enter {
  background: none;
  border: 1.5px solid #E8A33D;
  color: #E8A33D;
  padding: 7px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-enter:hover {
  background: #E8A33D;
  color: #fff;
}
.btn-join {
  background: #E8A33D;
  border: none;
  color: #fff;
  padding: 8px 24px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}
.btn-join:hover {
  background: #D4922E;
}
.btn-join:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Create Section */
.create-section {
  padding: 0 20px 40px;
}
.btn-create-toggle {
  width: 100%;
  background: #fff;
  border: 1.5px dashed #E0D8CE;
  color: #E8A33D;
  padding: 14px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-create-toggle:hover {
  border-color: #E8A33D;
  background: rgba(232, 163, 61, 0.04);
}

/* Create Form */
.create-form {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  margin-top: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #E0D8CE;
}
.form-field {
  margin-bottom: 16px;
}
.form-field label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #2D2A26;
  margin-bottom: 6px;
}
.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  border: 1px solid #E0D8CE;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  color: #2D2A26;
  background: #FFF9F0;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
  box-sizing: border-box;
}
.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  border-color: #E8A33D;
}
.form-field textarea {
  resize: vertical;
}
.btn-submit {
  width: 100%;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 13px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-submit:hover {
  background: #D4922E;
}
.btn-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
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
