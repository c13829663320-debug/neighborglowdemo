import axios from 'axios'
const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)
export const auth = {
  login: (username, password) => api.post('/auth/login', new URLSearchParams({ username, password })),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
}
export const cases = {
  create: (data) => api.post('/cases', data),
  list: (params) => api.get('/cases', { params }),
  get: (id) => api.get(`/cases/${id}`),
  update: (id, data) => api.put(`/cases/${id}`, data),
  remove: (id) => api.delete(`/cases/${id}`),
  diagnose: (id) => api.post(`/cases/${id}/diagnose`),
  confirmDiagnosis: (id, data) => api.post(`/cases/${id}/diagnose/confirm`, data),
  generatePlan: (id, data) => api.post(`/cases/${id}/plan`, data || {}),
  listPlans: (id) => api.get(`/cases/${id}/plans`),
  generateMessage: (id, data) => api.post(`/cases/${id}/messages/generate`, data),
  listMessages: (id) => api.get(`/cases/${id}/messages`),
  startSimulation: (id, data) => api.post(`/cases/${id}/simulations`, data),
  sendSimMessage: (id, simId, data) => api.post(`/cases/${id}/simulations/${simId}/messages`, data),
  createFollowup: (id, data) => api.post(`/cases/${id}/followups`, data),
  listFollowups: (id) => api.get(`/cases/${id}/followups`),
  escalate: (id) => api.post(`/cases/${id}/escalate`),
}
export const groups = {
  list: (params) => api.get('/groups', { params }),
  my: () => api.get('/groups/my'),
  get: (id) => api.get(`/groups/${id}`),
  create: (data) => api.post('/groups', data),
  update: (id, data) => api.put(`/groups/${id}`, data),
  join: (id) => api.post(`/groups/${id}/join`),
  leave: (id) => api.post(`/groups/${id}/leave`),
  members: (id) => api.get(`/groups/${id}/members`),
  topics: (id) => api.get(`/groups/${id}/topics`),
  createTopic: (id, data) => api.post(`/groups/${id}/topics`, data),
  chatHistory: (id, params) => api.get(`/groups/${id}/chat/history`, { params }),
  sendMessage: (id, data) => api.post(`/groups/${id}/chat/messages`, data),
  audit: (id) => api.get(`/groups/${id}/audit`),
}
export const items = {
  list: () => api.get('/items'),
  create: (data) => api.post('/items', data),
  remove: (id) => api.delete(`/items/${id}`),
}
export const serviceRequests = {
  list: (params) => api.get('/service-requests', { params }),
  handle: (id) => api.put(`/service-requests/${id}/handle`),
  complete: (id) => api.put(`/service-requests/${id}/complete`),
}
export const agents = {
  list: () => api.get('/agents'),
  trigger: (data) => api.post('/agent/trigger', data),
}
export const community = {
  overview: (params) => api.get('/community/overview', { params }),
  trends: (params) => api.get('/community/trends', { params }),
}
export default api
