import { ref } from 'vue'
import { doc, setDoc, updateDoc, arrayUnion } from 'firebase/firestore'
import { db } from '../firebase/index.js'
import { useStatusStore } from '../stores/status.js'
import { storeToRefs } from 'pinia'

// Firestore에 상태와 추가 데이터를 저장하는 composable
export function useUpdateDb() {
  const isLoading = ref(false)
  const error = ref(null)
  const statusStore = useStatusStore()
  const { user } = storeToRefs(statusStore)

  // Firestore에 데이터 저장
  // extraData: 추가로 저장하고 싶은 필드를 객체 형태로 전달
  const saveToDb = async () => {
    isLoading.value = true
    error.value = null
    try {
      if (!user.value) {
        throw new Error('로그인된 유저가 없습니다.')
      }
      // 저장할 데이터 객체 생성
      const data = {
        musicId: Array.isArray(statusStore.musicId)
          ? statusStore.musicId
          : statusStore.musicId.value,
        styleTag: Array.isArray(statusStore.styleTag)
          ? statusStore.styleTag
          : statusStore.styleTag.value,
        gender:
          typeof statusStore.gender === 'string' ? statusStore.gender : statusStore.gender.value,
        cloth: [],
      }
      const docRef = doc(db, 'prototype-data', user.value)
      await setDoc(docRef, data)
    } catch (e) {
      error.value = e
    } finally {
      isLoading.value = false
    }
  }

  // Firestore에 데이터 추가
  const addToDb = async (cloth) => {
    isLoading.value = true
    error.value = null
    try {
      if (!user.value) {
        throw new Error('로그인된 유저가 없습니다.')
      }
      const docRef = doc(db, 'prototype-data', user.value)
      await updateDoc(docRef, { cloth: arrayUnion(cloth) })
    } catch (e) {
      error.value = e
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    saveToDb,
    addToDb,
  }
}
