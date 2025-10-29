<script setup>
import { ref } from 'vue'

// const props = defineProps({
//   isVisible: {
//     type: Boolean,
//     default: true,
//   },
// })

const emit = defineEmits(['close-popup', 'confirm-popup'])

const selectedGender = ref('')

const selectGender = (gender) => {
  selectedGender.value = gender
}

const confirmSelection = () => {
  if (selectedGender.value) {
    emit('confirm-popup', selectedGender.value)
    closePopup()
  }
}

const closePopup = () => {
  selectedGender.value = ''
  emit('close-popup')
}
</script>

<template>
  <div class="gender-popup-overlay" @click="closePopup">
    <div class="gender-popup" @click.stop>
      <div class="popup-header">
        <h3>성별을 선택해주세요</h3>
        <button class="close-btn" @click="closePopup">&times;</button>
      </div>

      <div class="gender-options">
        <div
          class="gender-option"
          :class="{ selected: selectedGender === 'male' }"
          @click="selectGender('male')"
        >
          <div class="gender-icon">👨</div>
          <span>남성</span>
        </div>

        <div
          class="gender-option"
          :class="{ selected: selectedGender === 'female' }"
          @click="selectGender('female')"
        >
          <div class="gender-icon">👩</div>
          <span>여성</span>
        </div>
      </div>

      <div class="popup-actions">
        <button class="confirm-btn" @click="confirmSelection" :disabled="!selectedGender">
          확인
        </button>
        <button class="cancel-btn" @click="closePopup">취소</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gender-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.gender-popup {
  background: white;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  animation: popupSlideIn 0.3s ease-out;
}

@keyframes popupSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.popup-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f5f5f5;
  color: #666;
}

.gender-options {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.gender-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.gender-option:hover {
  border-color: #007bff;
  background: #f0f8ff;
  transform: translateY(-2px);
}

.gender-option.selected {
  border-color: #007bff;
  background: #e3f2fd;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2);
}

.gender-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.gender-option span {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.popup-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.confirm-btn,
.cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.confirm-btn {
  background: #007bff;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
}

.confirm-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.cancel-btn {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #dee2e6;
}

.cancel-btn:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

/* 모바일 반응형 */
/* @media (max-width: 480px) {
  .gender-popup {
    margin: 20px;
    padding: 20px;
  }

  .gender-options {
    flex-direction: column;
    gap: 12px;
  }

  .gender-option {
    padding: 16px;
  }

  .popup-actions {
    flex-direction: column;
  }

  .confirm-btn,
  .cancel-btn {
    width: 100%;
  }
} */
</style>
