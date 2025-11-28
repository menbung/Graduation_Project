import { ref } from 'vue'
import { doc, getDoc, collection, getDocs } from 'firebase/firestore'
import { db } from '../firebase/index.js'
import { useStatusStore } from '../stores/status.js'
import { useDataStore } from '@/stores/data.js'
import { storeToRefs } from 'pinia'

// Firestore에서 데이터를 가져와서 status store에 저장하는 composable
export function useGetDataDb() {
  const isLoading = ref(false)
  const error = ref(null)
  const dataStore = useDataStore()
  const { user, musicId, styleTag, gender } = storeToRefs(useStatusStore())

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

          // clothData 가져와서 data store에 저장
          for (const style of data.styleTag) {
            // style은 subcollection이므로 collection()을 사용해야 함
            const clothCollectionRef = collection(db, 'prototype-data', user.value, style)
            const clothQuerySnapshot = await getDocs(clothCollectionRef)

            if (!clothQuerySnapshot.empty) {
              const clothes = []
              clothQuerySnapshot.docs.forEach((doc) => {
                const clothData = doc.data()
                clothes.push({
                  img_id: clothData.img_id || '',
                  img_url: clothData.img_url || '',
                  web_url: clothData.web_url || '',
                })
              })
              dataStore.addClothData(clothes)
            } else {
              console.log(`저장된 문서가 존재하지 않습니다. (style: ${style})`)
            }
          }
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

  //음악 데이터 가져오기
  const loadMusicData = async () => {
    isLoading.value = true
    error.value = null
    try {
      const musicCollectionRef = collection(db, 'music-data')
      const musicQuerySnapshot = await getDocs(musicCollectionRef)

      if (!musicQuerySnapshot.empty) {
        musicQuerySnapshot.forEach((docSnap) => {
          const music = docSnap.data()
          dataStore.addMusicData({
            number: music.number ?? '',
            title: music.title ?? '',
            singer: music.singer ?? '',
            url: music.url ?? '',
          })
        })
      } else {
        console.log('music-data 컬렉션에 저장된 문서가 없습니다.')
      }
    } catch (e) {
      error.value = e
      console.error('음악 데이터 로드 중 오류 발생:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    loadFromDb,
    loadMusicData,
  }
}
