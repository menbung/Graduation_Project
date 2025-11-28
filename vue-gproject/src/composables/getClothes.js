import { ref } from 'vue'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { db } from '../firebase/index.js'
import { useDataStore } from '@/stores/data.js'
import { useStatusStore } from '@/stores/status.js'
import { useGetDownloadUrl } from './getDownloadUrl.js'
import { storeToRefs } from 'pinia'

export function useGetClothes() {
  const isLoading = ref(false)
  const error = ref(null)
  const dataStore = useDataStore()
  const statusStore = useStatusStore()
  const { user } = storeToRefs(statusStore)
  const { getImageDownloadUrl } = useGetDownloadUrl()

  /**
   * style에 해당하는 옷 데이터를 가져옵니다.
   * @param {string} style - 옷 스타일 (예: 'casual', 'formal' 등)
   * @returns {Promise<Array<{img_url: string, web_url: string}>>} 옷 데이터 배열
   */
  const getClothes = async (style) => {
    isLoading.value = true
    error.value = null

    try {
      // user 체크
      if (!user.value) {
        throw new Error('로그인된 유저가 없습니다.')
      }

      // count 문서에서 max_size 값 가져오기
      const countDocRef = doc(db, 'image-data', 'cloth', style, 'count')
      const countDocSnap = await getDoc(countDocRef)

      if (!countDocSnap.exists()) {
        throw new Error(`count 문서가 존재하지 않습니다: ${style}`)
      }

      const maxSize = countDocSnap.data().max_size

      if (!maxSize || maxSize < 1) {
        throw new Error(`유효하지 않은 max_size 값: ${maxSize}`)
      }

      const results = []

      // max_size가 10보다 작으면 모든 문서를 가져오기
      if (maxSize < 10) {
        for (let i = 1; i <= maxSize; i++) {
          const clothDocRef = doc(db, 'image-data', 'cloth', style, String(i))
          const clothDocSnap = await getDoc(clothDocRef)

          if (clothDocSnap.exists()) {
            const data = clothDocSnap.data()
            const urlPath = `cloth/${style}/${data.img_url}`
            let url = ''
            try {
              url = await getImageDownloadUrl(urlPath)
            } catch (urlError) {
              console.warn(`이미지 URL 가져오기 실패 (${urlPath}):`, urlError)
              // URL 가져오기 실패해도 계속 진행
            }
            results.push({
              img_id: String(i) || '',
              img_url: url || '',
              web_url: data.web_url || '',
            })
            const urlDocRef = doc(db, 'prototype-data', user.value, style, String(i - 1))
            await setDoc(urlDocRef, { img_id: String(i), img_url: url, web_url: data.web_url })
          }
        }
      } else {
        // max_size가 10 이상이면 랜덤하게 10개 선택
        const selectedNumbers = new Set()
        const maxAttempts = maxSize * 2 // 무한 루프 방지를 위한 최대 시도 횟수
        let attempts = 0

        while (selectedNumbers.size < 10 && attempts < maxAttempts) {
          attempts++
          const randomNum = Math.floor(Math.random() * maxSize) + 1

          // 이미 선택된 번호가 아니면 문서 확인
          if (!selectedNumbers.has(randomNum)) {
            const clothDocRef = doc(db, 'image-data', 'cloth', style, String(randomNum))
            const clothDocSnap = await getDoc(clothDocRef)

            if (clothDocSnap.exists()) {
              const data = clothDocSnap.data()
              const urlPath = `cloth/${style}/${data.img_url}`
              let url = ''
              try {
                url = await getImageDownloadUrl(urlPath)
              } catch (urlError) {
                console.warn(`이미지 URL 가져오기 실패 (${urlPath}):`, urlError)
                // URL 가져오기 실패해도 계속 진행
              }
              results.push({
                img_id: String(randomNum) || '',
                img_url: url || '',
                web_url: data.web_url || '',
              })
              const urlDocRef = doc(
                db,
                'prototype-data',
                user.value,
                style,
                String(selectedNumbers.size),
              )
              await setDoc(urlDocRef, {
                img_id: String(randomNum),
                img_url: url,
                web_url: data.web_url,
              })
              selectedNumbers.add(randomNum)
            }
          }
        }

        // 10개를 못 채운 경우 경고 (하지만 에러는 아님)
        if (results.length < 10) {
          console.warn(
            `요청한 10개의 문서 중 ${results.length}개만 가져올 수 있었습니다. (style: ${style}, max_size: ${maxSize})`,
          )
        }
      }

      dataStore.addClothData(results)
    } catch (e) {
      error.value = e
      console.error('옷 데이터 가져오기 실패:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    getClothes,
  }
}
