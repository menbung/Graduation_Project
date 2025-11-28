import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

async function healthCheck() {
  try {
    const res = await apiClient.get('/health')
    console.log('health: ', res.data)
  } catch (err) {
    console.log('health check error: ', err)
  }
}

async function postRecommend(payload) {
  try {
    const res = await apiClient.post('/recommend', payload)
    console.log('postRecommend response:', res.data)
    return res.data
  } catch (error) {
    // 서버가 { error, traceback } 형식으로 줄 수도 있으니 그거 먼저 확인
    if (error.response?.data) {
      console.error('postRecommend error response:', error.response.data)
      return error.response.data
    }

    console.error('postRecommend error:', error)
    throw error
  }
}

export { healthCheck, postRecommend }
