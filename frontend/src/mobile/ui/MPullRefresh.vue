<template>
  <div ref="scroller" class="m-ptr-scroll" @touchstart.passive="onStart" @touchmove.passive="onMove" @touchend="onEnd">
    <div class="m-ptr__ind" :style="indStyle">
      <Icon name="rotate-cw" :size="22" :class="{ 'm-ptr__spin': refreshing || pull > THRESH }" />
    </div>
    <div :style="{ transform: shift ? `translateY(${shift}px)` : '', transition: dragging ? 'none' : 'transform .25s' }">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Icon from '../../components/Icon.vue'

const props = defineProps({ refreshing: Boolean })
const emit = defineEmits(['refresh'])

const THRESH = 64
const scroller = ref(null)
const startY = ref(0)
const pull = ref(0)
const dragging = ref(false)

function onStart(e) {
  if (scroller.value && scroller.value.scrollTop <= 0) { startY.value = e.touches[0].clientY; dragging.value = true }
}
function onMove(e) {
  if (!dragging.value) return
  const dy = e.touches[0].clientY - startY.value
  pull.value = dy > 0 ? Math.min(dy * 0.5, 90) : 0
}
function onEnd() {
  if (dragging.value && pull.value > THRESH && !props.refreshing) emit('refresh')
  dragging.value = false; pull.value = 0
}

const shift = computed(() => (props.refreshing ? 44 : pull.value))
const indStyle = computed(() => ({ opacity: props.refreshing ? 1 : Math.min(pull.value / THRESH, 1), top: '8px' }))
</script>

<style scoped>
.m-ptr-scroll { height: 100%; overflow-y: auto; -webkit-overflow-scrolling: touch; position: relative; }
</style>
