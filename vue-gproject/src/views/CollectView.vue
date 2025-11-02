<script setup>
import { useRouter } from 'vue-router'
import { useStatusStore } from '@/stores/status'
import CollectMusic from '@/components/CollectMusic.vue'
import SelectGender from '@/components/SelectGender.vue'
import { ref } from 'vue'
import { useUpdateDb } from '@/composables/updateDb'

const router = useRouter()
const status = useStatusStore()
const isVisible = ref(false)
const updateDb = useUpdateDb()

function openPopup() {
  isVisible.value = true
}
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
  <div class="collect-main">
    <CollectMusic @open-popup="openPopup" />
    <SelectGender v-if="isVisible" @close-popup="closePopup" @confirm-popup="confirmPopup" />
  </div>
</template>

<style scoped></style>
