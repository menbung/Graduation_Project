<script setup>
import ClothResult from '../components/ClothResult.vue'
// import { ref } from 'vue'
import { useStatusStore } from '@/stores/status'
import { storeToRefs } from 'pinia'

const status = useStatusStore()
const { styleTag } = storeToRefs(status)
</script>

<template>
  <div class="home-main" v-for="(category, index) in styleTag" :key="index">
    <ClothResult :number="index + 1" :category="category" />
  </div>
</template>
