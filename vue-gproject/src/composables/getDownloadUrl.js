import { ref } from 'vue'
import { getStorage, ref as storageRef, getDownloadURL } from 'firebase/storage'
import { app } from '../firebase/index.js'

// Firebase Storage에서 이미지의 다운로드 URL을 가져오는 composable
export function useGetDownloadUrl() {
  const isLoading = ref(false)
  const error = ref(null)

  // Firebase Storage 인스턴스 가져오기
  const storage = getStorage(app)

  /**
   * Firebase Storage에서 이미지의 다운로드 URL을 가져옵니다.
   * @param {string} imagePath - Storage 내 이미지 경로 (예: 'music_thumbnail/1_zay.jpg')
   * @returns {Promise<string>} 이미지의 다운로드 URL
   */
  const getImageDownloadUrl = async (imagePath) => {
    isLoading.value = true
    error.value = null
    try {
      // Storage 참조 생성
      const imageRef = storageRef(storage, imagePath)

      // 다운로드 URL 가져오기
      const downloadURL = await getDownloadURL(imageRef)

      return downloadURL
    } catch (e) {
      error.value = e
      console.error('이미지 URL 가져오기 실패:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    getImageDownloadUrl,
  }
}
