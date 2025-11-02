import { ref } from 'vue'
import { doc, getDoc } from 'firebase/firestore'
import { db } from '../firebase/index.js'
import { useStatusStore } from '../stores/status.js'
import { storeToRefs } from 'pinia'

// Firestore에서 데이터를 가져와서 status store에 저장하는 composable
export function useGetDataDb() {
  const isLoading = ref(false)
  const error = ref(null)
  const statusStore = useStatusStore()
  const { user, musicId, styleTag, gender } = storeToRefs(statusStore)

  // Firestore에서 유저 문서를 가져와서 status store에 저장
  const loadFromDb = async () => {
    isLoading.value = true
    error.value = null
    try {
      if (!user.value) {
        throw new Error('로그인된 유저가 없습니다.')
      }
      const docRef = doc(db, 'prototype-data', user.value)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        const data = docSnap.data()
        // cloth 필드는 제외하고 나머지 필드들을 status store에 저장
        if (data.musicId !== undefined) {
          musicId.value = Array.isArray(data.musicId) ? data.musicId : []
        }
        if (data.styleTag !== undefined) {
          styleTag.value = Array.isArray(data.styleTag) ? data.styleTag : []
        }
        if (data.gender !== undefined) {
          gender.value = data.gender
        }
      } else {
        console.log('문서가 존재하지 않습니다.')
      }
    } catch (e) {
      error.value = e
      console.error('데이터 로드 중 오류 발생:', e)
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    loadFromDb,
  }
}
