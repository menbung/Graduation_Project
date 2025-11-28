import { ref } from 'vue'
import { doc, setDoc } from 'firebase/firestore'
import { db } from '../firebase/index.js'
import { useGetDownloadUrl } from './getDownloadUrl.js'
import ClothTable from '../assets/tables/ClothTable.json'
import SongsTable from '../assets/tables/SongsTable.json'

// ClothTable.json의 데이터를 Firestore에 저장하는 composable
export function useUpdateTable() {
  const isLoading = ref(false)
  const error = ref(null)
  const progress = ref({ current: 0, total: 0 })
  const { getImageDownloadUrl } = useGetDownloadUrl()

  // ClothTable.json의 모든 데이터를 Firestore에 저장
  const saveClothTableToFirestore = async () => {
    isLoading.value = true
    error.value = null
    progress.value = { current: 0, total: ClothTable.length }

    try {
      // ClothTable의 각 항목을 순회하며 Firestore에 저장
      for (let i = 0; i < ClothTable.length; i++) {
        const item = ClothTable[i]
        const { style, number, img_url, web_url } = item

        // image-data/cloth/{style}/{number} 경로로 문서 생성
        const docRef = doc(db, 'image-data', 'cloth', style, number)

        // img_url과 web_url 필드를 가진 문서 저장
        await setDoc(docRef, {
          img_url,
          web_url,
        })

        progress.value.current = i + 1
      }

      console.log('ClothTable 데이터가 성공적으로 Firestore에 저장되었습니다.')
    } catch (e) {
      error.value = e
      console.error('ClothTable 저장 중 오류 발생:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  //SongsTable의 내용을 url링크와 함께 저장
  const saveMusicTableToFirebase = async () => {
    for (let i = 0; i < SongsTable.length; i++) {
      const song = SongsTable[i]
      const { number, title, singer, thumbnail_url } = song
      if (thumbnail_url) {
        try {
          const imagePath = `music_thumbnail/${thumbnail_url}`
          const url = await getImageDownloadUrl(imagePath)
          const docRef = doc(db, 'music-data', String(i))
          await setDoc(docRef, {
            number,
            title,
            singer,
            url,
          })
        } catch (error) {
          console.error(`이미지 URL 가져오기 실패 (인덱스 ${i}):`, error)
        }
      }
    }
  }

  return {
    isLoading,
    error,
    progress,
    saveClothTableToFirestore,
    saveMusicTableToFirebase,
  }
}
