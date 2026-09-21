import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
}

export const chatAPI = {
  sendMessage: (data) => api.post('/chat/send', data),
  getThreads: (customerId) => api.get(`/chat/threads/${customerId}`),
  getMessages: (threadId) => api.get(`/chat/messages/${threadId}`),
  createThread: (data) => api.post('/chat/threads', data),
}

export const agentAPI = {
  getLogs: (threadId) => api.get(`/agents/logs/${threadId}`),
  getRuns: (threadId) => api.get(`/agents/runs/${threadId}`),
  getStats: () => api.get('/agents/stats'),
}

export default api
