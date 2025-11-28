<script setup>
import { useRouter } from 'vue-router'
import { useStatusStore } from '@/stores/status'
import CollectMusic from '@/components/CollectMusic.vue'
import SelectGender from '@/components/SelectGender.vue'
import LoadingView from '@/components/LoadingView.vue'
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useUpdateDb } from '@/composables/updateDb'
import { callModel1 } from '@/api/callPost'
import { useGetClothes } from '@/composables/getClothes'

const router = useRouter()
const status = useStatusStore()
const isVisible = ref(false)
const updateDb = useUpdateDb()
const isLoading = ref(false)
const { musicId, styleTag } = storeToRefs(status)
const { getClothes } = useGetClothes()

async function callApi() {
  isLoading.value = true
  //api를 통해 추천 스타일 3개 리스트로 받아오기
  styleTag.value = await callModel1(musicId.value)
  //유저 정보 저장
  updateDb.saveToDb()
  // styleTag 값을 가져와서 각 style에 대한 옷 데이터를 가져와 db에 추가
  const styleTags = styleTag.value
  if (styleTags && styleTags.length > 0) {
    for (const styleTag of styleTags) {
      try {
        await getClothes(styleTag)
      } catch (error) {
        console.error(`옷 데이터 가져오기 실패 (style: ${styleTag}):`, error)
      }
    }
  }
  isLoading.value = false
  router.push('/main')
}
// function openPopup() {
//   isVisible.value = true
// }
function closePopup() {
  isVisible.value = false
}

function confirmPopup(gender) {
  status.inputGender(gender)
  updateDb.saveToDb()
  router.push('/main')
}
</script>

<template>
  <LoadingView v-if="isLoading">
    <template #text>분석 중...</template>
  </LoadingView>
  <div class="collect-main">
    <!-- <CollectMusic @open-popup="openPopup" /> -->
    <CollectMusic @call-api="callApi" />
    <SelectGender v-if="isVisible" @close-popup="closePopup" @confirm-popup="confirmPopup" />
  </div>
</template>

<style scoped></style>
