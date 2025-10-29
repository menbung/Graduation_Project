<script setup>
import ClothResult from '../components/ClothResult.vue'
import { ref } from 'vue'

const categories = ref(['테스트1', '테스트2', '테스트3'])
</script>

<template>
  <div class="home-main" v-for="(category, index) in categories" :key="index">
    <ClothResult :number="index + 1" :category="categories[index]" />
  </div>
</template>
