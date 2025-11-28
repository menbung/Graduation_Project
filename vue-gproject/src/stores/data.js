import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useDataStore = defineStore('data', () => {
  //추천 옷 데이터 저장
  const clothData = ref([])
  //음악 데이터 저장
  const musicData = ref([])

  const getClothData = computed(() => clothData.value)

  function addClothData(cloth) {
    clothData.value.push(cloth)
  }
  function removeClothData(cloth) {
    clothData.value = clothData.value.filter((item) => item !== cloth)
  }

  function addMusicData(music) {
    musicData.value.push(music)
  }

  return {
    clothData,
    musicData,
    getClothData,
    addClothData,
    removeClothData,
    addMusicData,
  }
})
