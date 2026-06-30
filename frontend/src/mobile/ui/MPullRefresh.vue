<template>
  <!--
    Lưu ý layout: phần tử cha PHẢI có chiều cao giới hạn (vd 100dvh trừ topbar/tabbar)
    để .m-ptr-scroll có thể scroll nội bộ. Nếu cha không giới hạn chiều cao, body cuộn
    thay vì scroller → scrollTop luôn =0 → PTR bị kích nhầm mọi cú vuốt xuống.
  -->
  <div
    ref="scroller"
    class="m-ptr-scroll"
    @touchstart.passive="onStart"
    @touchmove.passive="onMove"
    @touchend="onEnd"
    @touchcancel="onEnd"
  >
    <div class="m-ptr__ind" :style="indStyle">
      <Icon
        name="rotate-cw"
        :size="22"
        :class="{ 'm-ptr__spin': refreshing && triggered }"
        :style="!(refreshing && triggered) && pull > 0
          ? { transform: `rotate(${Math.min(pull / THRESH, 1) * 180}deg)`, transition: 'transform .05s' }
          : {}"
      />
    </div>
    <div :style="{ transform: shift ? `translateY(${shift}px)` : '', transition: dragging ? 'none' : 'transform .25s' }">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Icon from '../../components/Icon.vue'

const props = defineProps({ refreshing: Boolean })
const emit = defineEmits(['refresh'])

const THRESH = 64
const scroller = ref(null)
const startY   = ref(0)
const pull     = ref(0)
const dragging = ref(false)
// triggered: phân biệt refresh do kéo thả vs loading từ nguồn ngoài.
// Chỉ đặt true khi người dùng thực sự thả sau khi kéo vượt ngưỡng.
const triggered = ref(false)

function onStart(e) {
  if (scroller.value && scroller.value.scrollTop <= 0) {
    startY.value = e.touches[0].clientY
    dragging.value = true
  }
}
function onMove(e) {
  if (!dragging.value) return
  const dy = e.touches[0].clientY - startY.value
  pull.value = dy > 0 ? Math.min(dy * 0.5, 90) : 0
}
function onEnd() {
  if (dragging.value && pull.value > THRESH && !props.refreshing) {
    triggered.value = true
    emit('refresh')
  }
  dragging.value = false
  pull.value = 0
}

// Reset triggered khi refreshing kết thúc (prop về false)
watch(() => props.refreshing, (val) => {
  if (!val) triggered.value = false
})

// Chỉ đẩy nội dung xuống khi đang refresh do chính PTR kích hoạt
const shift    = computed(() => (props.refreshing && triggered.value ? 44 : pull.value))
const indStyle = computed(() => ({
  opacity: props.refreshing ? 1 : Math.min(pull.value / THRESH, 1),
  top: '8px',
}))
</script>

<style scoped>
.m-ptr-scroll { height: 100%; overflow-y: auto; -webkit-overflow-scrolling: touch; position: relative; }
</style>
