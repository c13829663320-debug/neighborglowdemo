import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/resident', name: 'ResidentDashboard', component: () => import('../views/resident/Dashboard.vue'), meta: { requiresRole: 'resident' } },
  { path: '/resident/submit', name: 'SubmitRequest', component: () => import('../views/resident/SubmitRequest.vue'), meta: { requiresRole: 'resident' } },
  { path: '/resident/my-requests', name: 'MyRequests', component: () => import('../views/resident/MyRequests.vue'), meta: { requiresRole: 'resident' } },
  { path: '/resident/groups', name: 'GroupsNearby', component: () => import('../views/resident/GroupsNearby.vue'), meta: { requiresRole: 'resident' } },
  { path: '/resident/groups/my', name: 'MyGroups', component: () => import('../views/resident/MyGroups.vue'), meta: { requiresRole: 'resident' } },
  { path: '/resident/groups/:id', name: 'GroupDetail', component: () => import('../views/resident/GroupDetail.vue'), meta: { requiresRole: 'resident' } },
  { path: '/resident/groups/:id/chat', name: 'GroupChat', component: () => import('../views/resident/Chat.vue'), meta: { requiresRole: 'resident' } },
  { path: '/staff', name: 'StaffDashboard', component: () => import('../views/staff/Dashboard.vue'), meta: { requiresRole: 'staff' } },
  { path: '/staff/tickets', name: 'TicketList', component: () => import('../views/staff/TicketList.vue'), meta: { requiresRole: 'staff' } },
  { path: '/staff/items', name: 'ItemManagement', component: () => import('../views/staff/ItemManagement.vue'), meta: { requiresRole: 'staff' } },
]
const router = createRouter({
  history: createWebHistory(),
  routes,
})
router.beforeEach((to, from, next) => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || 'null')
  const token = localStorage.getItem('token')
  if (to.path === '/login' || to.path === '/register') {
    if (token && userInfo) {
      next(userInfo.role === 'resident' ? '/resident' : '/staff')
    } else {
      next()
    }
    return
  }
  if (!token || !userInfo) {
    next('/login')
    return
  }
  if (to.meta.requiresRole && to.meta.requiresRole !== userInfo.role) {
    next(userInfo.role === 'resident' ? '/resident' : '/staff')
    return
  }
  next()
})
export default router
