<template>
  <div class="page">
    <!-- Toast -->
    <transition name="toast-fade">
      <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.msg }}</div>
    </transition>

    <!-- Top Bar -->
    <header class="top-bar">
      <button class="btn-back" @click="$router.push('/staff')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        返回
      </button>
      <h1 class="page-title">物品管理</h1>
      <button class="btn-add-top" @click="showAddForm = true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      </button>
    </header>

    <!-- Add Item Form -->
    <transition name="form-slide">
      <section v-if="showAddForm" class="add-form">
        <h3 class="form-title">添加新物品</h3>
        <div class="form-group">
          <label class="form-label">物品名称</label>
          <input v-model="form.title" class="form-input" placeholder="例如：失物招领 - 黑色钱包" maxlength="60" />
        </div>
        <div class="form-group">
          <label class="form-label">描述</label>
          <textarea v-model="form.description" class="form-textarea" placeholder="描述物品详情、发现地点、时间等..." rows="3" maxlength="300"></textarea>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="closeForm">取消</button>
          <button class="btn-submit" :disabled="!form.title.trim() || submitLoading" @click="addItem">
            <div v-if="submitLoading" class="spinner-sm"></div>
            <template v-else>添加物品</template>
          </button>
        </div>
      </section>
    </transition>

    <!-- Stats -->
    <section class="stats-row">
      <div class="stat-item">
        <span class="stat-num">{{ itemsList.length }}</span>
        <span class="stat-label">物品总数</span>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading && itemsList.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>加载物品列表...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="itemsList.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#E0D8CE" stroke-width="1.5"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
      </div>
      <p class="empty-text">暂无物品记录</p>
      <p class="empty-hint">点击上方 + 按钮添加失物招领或物品信息</p>
    </div>

    <!-- Items List -->
    <section v-else class="items-list">
      <div v-for="item in itemsList" :key="item.id" class="item-card">
        <div class="item-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
        </div>
        <div class="item-body">
          <h4 class="item-title">{{ item.title }}</h4>
          <p class="item-desc" v-if="item.description">{{ item.description }}</p>
        </div>
        <button class="btn-delete" @click="confirmDelete(item)" :disabled="deleteId === item.id">
          <template v-if="deleteId === item.id">
            <div class="spinner-sm spinner-red"></div>
          </template>
          <template v-else>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
          </template>
        </button>
      </div>
    </section>

    <!-- Delete Confirm Modal -->
    <transition name="modal-fade">
      <div v-if="deleteModal.show" class="modal-overlay" @click.self="deleteModal.show = false">
        <div class="modal-box">
          <h3 class="modal-title">确认删除</h3>
          <p class="modal-desc">确定删除物品「<strong>{{ deleteModal.item?.title }}</strong>」？此操作不可撤销。</p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="deleteModal.show = false">取消</button>
            <button class="btn-modal-confirm" :disabled="deleteId !== null" @click="doDelete">确认删除</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { items as itemsApi } from '../../api'

const loading = ref(false)
const submitLoading = ref(false)
const deleteId = ref(null)
const showAddForm = ref(false)
const itemsList = ref([])
const form = ref({ title: '', description: '' })
const deleteModal = ref({ show: false, item: null })
const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

async function loadItems() {
  loading.value = true
  try {
    const res = await itemsApi.list()
    itemsList.value = Array.isArray(res.data) ? res.data : []
  } catch {
    showToast('加载物品列表失败', 'error')
    itemsList.value = []
  } finally {
    loading.value = false
  }
}

function closeForm() {
  showAddForm.value = false
  form.value = { title: '', description: '' }
}

async function addItem() {
  if (!form.value.title.trim()) return
  submitLoading.value = true
  try {
    await itemsApi.create({
      title: form.value.title.trim(),
      description: form.value.description.trim() || null
    })
    showToast('物品添加成功')
    closeForm()
    await loadItems()
  } catch {
    showToast('添加失败，请重试', 'error')
  } finally {
    submitLoading.value = false
  }
}

function confirmDelete(item) {
  deleteModal.value = { show: true, item }
}

async function doDelete() {
  const item = deleteModal.value.item
  if (!item) return
  deleteModal.value.show = false
  deleteId.value = item.id
  try {
    await itemsApi.remove(item.id)
    itemsList.value = itemsList.value.filter(i => i.id !== item.id)
    showToast('已删除')
  } catch {
    showToast('删除失败，请重试', 'error')
  } finally {
    deleteId.value = null
  }
}

onMounted(() => { loadItems() })
onBeforeUnmount(() => { clearTimeout(toastTimer) })
</script>

<style scoped>
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #FFF9F0;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  color: #2D2A26;
  padding-bottom: 32px;
}

/* Toast */
.toast {
  position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px 24px; border-radius: 24px;
  font-size: 13px; font-weight: 500; box-shadow: 0 4px 16px rgba(0,0,0,0.12); white-space: nowrap;
}
.toast-success { background: #2D2A26; color: #fff; }
.toast-error { background: #FF3B30; color: #fff; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* Top Bar */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #fff; border-bottom: 1px solid #E0D8CE;
  position: sticky; top: 0; z-index: 50;
}
.btn-back {
  display: flex; align-items: center; gap: 4px;
  background: none; border: none; color: #E8A33D; font-size: 14px; font-weight: 500;
  cursor: pointer; padding: 4px 0;
}
.page-title { font-size: 17px; font-weight: 700; margin: 0; }
.btn-add-top {
  width: 34px; height: 34px; border-radius: 8px; border: 1px solid #E8A33D;
  background: #E8A33D; color: #fff; display: flex; align-items: center;
  justify-content: center; cursor: pointer; transition: all 0.2s;
}
.btn-add-top:hover { background: #D4922F; }

/* Add Form */
.add-form {
  margin: 12px 16px; padding: 16px; background: #fff;
  border: 1px solid #E0D8CE; border-radius: 12px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}
.form-title { font-size: 15px; font-weight: 600; margin: 0 0 14px; }
.form-group { margin-bottom: 12px; }
.form-label { display: block; font-size: 12px; font-weight: 600; color: #6B6560; margin-bottom: 6px; }
.form-input {
  width: 100%; padding: 10px 12px; border: 1px solid #E0D8CE; border-radius: 8px;
  font-size: 14px; color: #2D2A26; background: #fff; outline: none;
  transition: border-color 0.2s; box-sizing: border-box;
}
.form-input:focus { border-color: #E8A33D; }
.form-input::placeholder { color: #B8AFA3; }
.form-textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #E0D8CE; border-radius: 8px;
  font-size: 14px; color: #2D2A26; background: #fff; outline: none;
  resize: vertical; min-height: 70px; transition: border-color 0.2s;
  box-sizing: border-box; font-family: inherit;
}
.form-textarea:focus { border-color: #E8A33D; }
.form-textarea::placeholder { color: #B8AFA3; }
.form-actions { display: flex; gap: 10px; margin-top: 14px; }
.btn-cancel {
  flex: 1; padding: 10px; border: 1px solid #E0D8CE; border-radius: 10px;
  background: #fff; font-size: 14px; color: #6B6560; cursor: pointer;
}
.btn-cancel:hover { background: #F5F0E8; }
.btn-submit {
  flex: 1; padding: 10px; border: none; border-radius: 10px;
  background: #E8A33D; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  gap: 6px; transition: background 0.2s;
}
.btn-submit:hover:not(:disabled) { background: #D4922F; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.form-slide-enter-active, .form-slide-leave-active { transition: all 0.3s ease; }
.form-slide-enter-from, .form-slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* Stats */
.stats-row {
  padding: 12px 16px 4px;
}
.stat-item {
  background: #fff; border: 1px solid #E0D8CE; border-radius: 12px;
  padding: 12px 16px; display: flex; align-items: center; gap: 10px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}
.stat-num { font-size: 22px; font-weight: 700; color: #E8A33D; }
.stat-label { font-size: 13px; color: #6B6560; }

/* Loading & Empty */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 20px; color: #6B6560; gap: 12px;
}
.loading-state p { font-size: 14px; margin: 0; }
.spinner {
  width: 32px; height: 32px; border: 3px solid #E0D8CE;
  border-top-color: #E8A33D; border-radius: 50%; animation: spin 0.8s linear infinite;
}
.spinner-sm {
  width: 16px; height: 16px; border: 2px solid #E0D8CE;
  border-top-color: #E8A33D; border-radius: 50%; animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
.spinner-red { border-top-color: #FF3B30; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px 24px; text-align: center;
}
.empty-icon { margin-bottom: 16px; opacity: 0.6; }
.empty-text { font-size: 15px; font-weight: 500; color: #2D2A26; margin: 0 0 6px; }
.empty-hint { font-size: 13px; color: #6B6560; margin: 0; }

/* Items List */
.items-list {
  padding: 8px 16px; display: flex; flex-direction: column; gap: 10px;
}
.item-card {
  display: flex; align-items: flex-start; gap: 12px;
  background: #fff; border: 1px solid #E0D8CE; border-radius: 12px;
  padding: 14px; box-shadow: 0 1px 8px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.item-card:hover { box-shadow: 0 2px 12px rgba(232,163,61,0.1); }
.item-icon {
  width: 40px; height: 40px; border-radius: 10px; background: #FFF9F0;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.item-body { flex: 1; min-width: 0; }
.item-title {
  font-size: 14px; font-weight: 600; color: #2D2A26; margin: 0 0 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.item-desc {
  font-size: 12px; color: #6B6560; line-height: 1.5; margin: 0;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}
.btn-delete {
  flex-shrink: 0; width: 34px; height: 34px; border-radius: 8px;
  border: 1px solid #E0D8CE; background: #fff; color: #999;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s;
}
.btn-delete:hover { border-color: #FF3B30; color: #FF3B30; background: #FFF5F5; }
.btn-delete:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.modal-box {
  background: #fff; border-radius: 16px; padding: 24px;
  width: 100%; max-width: 340px; box-shadow: 0 12px 40px rgba(0,0,0,0.15);
}
.modal-title { font-size: 16px; font-weight: 600; margin: 0 0 12px; }
.modal-desc { font-size: 14px; color: #4A4540; line-height: 1.6; margin: 0 0 20px; }
.modal-actions { display: flex; gap: 10px; }
.btn-modal-cancel {
  flex: 1; padding: 10px; border: 1px solid #E0D8CE; border-radius: 10px;
  background: #fff; font-size: 14px; color: #6B6560; cursor: pointer;
}
.btn-modal-cancel:hover { background: #F5F0E8; }
.btn-modal-confirm {
  flex: 1; padding: 10px; border: none; border-radius: 10px;
  background: #FF3B30; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.2s;
}
.btn-modal-confirm:hover:not(:disabled) { background: #E0332A; }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all 0.25s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
