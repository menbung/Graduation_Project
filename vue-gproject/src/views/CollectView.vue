<script setup>
import CollectMusic from '@/components/CollectMusic.vue'
import SelectGender from '@/components/SelectGender.vue'
import { ref } from 'vue'

const isVisible = ref(false)

function openPopup() {
  isVisible.value = true
}
function closePopup() {
  isVisible.value = false
}

function confirmPopup() {
  closePopup
}
</script>

<template>
  <div class="collect-main">
    <CollectMusic @open-popup="openPopup" />
    <SelectGender v-if="isVisible" @close-popup="closePopup" @confirm="confirmPopup" />
  </div>
</template>

<style scoped></style>
