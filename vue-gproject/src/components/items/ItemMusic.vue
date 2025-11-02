<script setup>
import { ref, onMounted, nextTick } from 'vue'

const isOnClick = ref(false)
// 음악 가수명과 제목 요소에 대한 참조 (롤링 효과를 위한 너비 확인용)
const singerRef = ref(null)
const titleRef = ref(null)
const emit = defineEmits(['add-count', 'sub-count'])
const props = defineProps({
  count: {
    typeof: Number,
    default: 0,
  },
  id: {
    typeof: Number,
    default: 0,
  },
})

function onClick() {
  if (isOnClick.value) {
    isOnClick.value = false
    emit('sub-count', props.id)
  } else if (props.count < 3) {
    isOnClick.value = true
    emit('add-count', props.id)
  }
}

// 요소의 텍스트가 컨테이너 너비를 넘는지 확인하고 롤링 효과 활성화
function checkAndEnableScroll(element) {
  if (!element) return

  // 내부의 rolling-container를 찾아서 실제 텍스트 너비 확인
  const container = element.querySelector('.rolling-container')
  if (!container) return

  const firstText = container.querySelector('.rolling-text:first-child')
  if (!firstText) return

  // 첫 번째 텍스트의 실제 너비와 부모 컨테이너의 너비 비교
  const textWidth = firstText.scrollWidth
  const containerWidth = element.clientWidth

  if (textWidth > containerWidth) {
    element.classList.add('needs-scroll')
  }
}

// 컴포넌트 마운트 시 가수명과 제목의 너비를 확인하여 필요시 롤링 효과 적용
// nextTick을 사용하여 슬롯 내용이 완전히 렌더링된 후 체크
onMounted(async () => {
  await nextTick()
  if (singerRef.value) {
    checkAndEnableScroll(singerRef.value)
  }
  if (titleRef.value) {
    checkAndEnableScroll(titleRef.value)
  }
})
</script>

<template>
  <article class="item-music" :class="{ check: isOnClick }" @click="onClick">
    <div class="music-img" aria-hidden="true"></div>
    <div class="music-singer" ref="singerRef">
      <!-- 롤링 효과를 위한 컨테이너: 텍스트를 두 번 복제하여 무한 반복 효과 구현 -->
      <div class="rolling-container">
        <span class="rolling-text">
          <slot name="singer"></slot>
        </span>
        <!-- 두 번째 복제된 텍스트 (무한 롤링을 위해 필요) -->
        <span class="rolling-text" aria-hidden="true">
          <slot name="singer"></slot>
        </span>
      </div>
    </div>
    <div class="music-title" ref="titleRef">
      <!-- 롤링 효과를 위한 컨테이너: 텍스트를 두 번 복제하여 무한 반복 효과 구현 -->
      <div class="rolling-container">
        <span class="rolling-text">
          <slot name="title"></slot>
        </span>
        <!-- 두 번째 복제된 텍스트 (무한 롤링을 위해 필요) -->
        <span class="rolling-text" aria-hidden="true">
          <slot name="title"></slot>
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.item-music {
  flex: none;
  width: 100px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.check {
  background-color: var(--brand-color);
  color: #000000;
}
.music-img {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #e8e8e8;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-size: cover;
  background-position: center;
}
.music-singer,
.music-title {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  width: 100%;
  text-align: center;
  position: relative;
}

/* 롤링 컨테이너: 복제된 텍스트들을 담는 flex 컨테이너 */
.music-singer .rolling-container,
.music-title .rolling-container {
  display: inline-flex;
  width: max-content;
  min-width: 100%;
}

/* 롤링 텍스트: 개별 텍스트 요소 스타일 */
.music-singer .rolling-text,
.music-title .rolling-text {
  display: inline-block;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 텍스트가 길 때: 롤링 애니메이션 적용 (오른쪽에서 왼쪽으로 n초 주기 무한 반복) */
.music-singer.needs-scroll .rolling-container,
.music-title.needs-scroll .rolling-container {
  animation: roll-right-to-left 10s linear infinite;
  will-change: transform;
}

/* 롤링 애니메이션이 적용될 때 텍스트 간 간격 추가 */
.music-singer.needs-scroll .rolling-text,
.music-title.needs-scroll .rolling-text {
  padding-right: 30px;
}

/* 롤링 애니메이션: 오른쪽에서 왼쪽으로 이동 */
/* 첫 번째 텍스트 너비만큼 이동하여 두 번째 텍스트가 시작 위치로 오도록 함 */
@keyframes roll-right-to-left {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(calc(-50% - 15px));
  }
}

/* 텍스트가 짧을 때: 롤링 효과 없이 중앙 정렬 및 오버플로우 처리 */
.music-singer:not(.needs-scroll) .rolling-container,
.music-title:not(.needs-scroll) .rolling-container {
  justify-content: center;
  overflow: hidden;
}

/* 텍스트가 짧을 때: 첫 번째 텍스트만 표시하고 ellipsis 처리 */
.music-singer:not(.needs-scroll) .rolling-text:first-child,
.music-title:not(.needs-scroll) .rolling-text:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  display: block;
}

/* 텍스트가 짧을 때: 두 번째 복제된 텍스트 숨김 */
.music-singer:not(.needs-scroll) .rolling-text:last-child,
.music-title:not(.needs-scroll) .rolling-text:last-child {
  display: none;
}
</style>
