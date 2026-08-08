import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8999/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Optional single-token guard: if the backend sets FD_BENCH_API_TOKEN,
// put the same value in localStorage key `fd_bench_api_token`.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fd_bench_api_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default api
