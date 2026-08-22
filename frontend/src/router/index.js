import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/resident', name: 'ResidentDashboard', component: () => import('../views/resident/Dashboard.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/submit', name: 'SubmitRequest', component: () => import('../views/resident/SubmitRequest.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/my-requests', name: 'MyRequests', component: () => import('../views/resident/MyRequests.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/case/:id', name: 'CaseDetail', component: () => import('../views/resident/CaseDetail.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/case/:id/diagnosis', name: 'DiagnosisResult', component: () => import('../views/resident/DiagnosisResult.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/case/:id/plan', name: 'ActionPlan', component: () => import('../views/resident/ActionPlan.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/case/:id/messages', name: 'MessageGeneration', component: () => import('../views/resident/MessageGeneration.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/case/:id/simulation', name: 'SimulationTraining', component: () => import('../views/resident/SimulationTraining.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/case/:id/followup', name: 'FollowUp', component: () => import('../views/resident/FollowUp.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/groups', name: 'GroupsNearby', component: () => import('../views/resident/GroupsNearby.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/groups/my', name: 'MyGroups', component: () => import('../views/resident/MyGroups.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/groups/:id', name: 'GroupDetail', component: () => import('../views/resident/GroupDetail.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/resident/groups/:id/chat', name: 'GroupChat', component: () => import('../views/resident/Chat.vue'), meta: { requiresAuth: true, requiresRole: 'resident' } },
  { path: '/staff', name: 'StaffDashboard', component: () => import('../views/staff/Dashboard.vue'), meta: { requiresAuth: true, requiresRole: 'staff' } },
  { path: '/staff/tickets', name: 'TicketList', component: () => import('../views/staff/TicketList.vue'), meta: { requiresAuth: true, requiresRole: 'staff' } },
  { path: '/staff/items', name: 'ItemManagement', component: () => import('../views/staff/ItemManagement.vue'), meta: { requiresAuth: true, requiresRole: 'staff' } },
]
const router = createRouter({
  history: createWebHistory(),
  routes,
})

function clearSession() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
}

function getValidSession() {
  const token = localStorage.getItem('token')
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || 'null')
  if (!token || !userInfo || !userInfo.role) {
    clearSession()
    return null
  }
  return { token, userInfo }
}

function getDefaultRoute(role) {
  return role === 'staff' ? '/staff' : '/resident'
}

router.beforeEach((to, from, next) => {
  const session = getValidSession()

  if (to.path === '/login' || to.path === '/register') {
    if (session) {
      next(getDefaultRoute(session.userInfo.role))
    } else {
      next()
    }
    return
  }

  if (!session) {
    next('/login')
    return
  }

  if (to.meta.requiresRole && to.meta.requiresRole !== session.userInfo.role) {
    next(getDefaultRoute(session.userInfo.role))
    return
  }

  next()
})
export default router
