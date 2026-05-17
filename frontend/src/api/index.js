import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Schedules
export const listSchedules = () => api.get('/schedules').then(r => r.data)
export const createSchedule = (data) => api.post('/schedules', data).then(r => r.data)
export const importSchedules = (items) => api.post('/schedules/import', items).then(r => r.data)
export const exportSchedules = (ids = []) => api.get('/schedules/export', { params: ids.length ? { ids: ids.join(',') } : {}, responseType: 'blob' }).then(r => r.data)
export const updateSchedule = (id, data) => api.put(`/schedules/${id}`, data).then(r => r.data)
export const deleteSchedule = (id) => api.delete(`/schedules/${id}`)
export const batchDeleteSchedules = (ids) => api.post('/schedules/batch-delete', ids)
export const toggleSchedule = (id) => api.post(`/schedules/${id}/toggle`).then(r => r.data)
export const triggerSchedule = (id) => api.post(`/schedules/${id}/trigger`).then(r => r.data)
export const testConnection = (data) => api.post('/schedules/test-connection', data).then(r => r.data)

// Runs
export const listRuns = (params) => api.get('/runs', { params }).then(r => r.data) // job_id, search, limit
export const getRun = (id) => api.get(`/runs/${id}`).then(r => r.data)
export const deleteRuns = (ids) => api.post('/runs/delete', { ids }).then(r => r.data)
export const cancelRun = (id) => api.post(`/runs/${id}/cancel`).then(r => r.data)

// Benchmarks
export const listPresets = () => api.get('/benchmarks/presets').then(r => r.data)
export const listCategories = () => api.get('/benchmarks/categories').then(r => r.data)
