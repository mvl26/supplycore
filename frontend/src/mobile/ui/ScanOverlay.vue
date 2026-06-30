<template>
  <teleport to="body">
    <transition name="sc-ov">
      <div v-if="scanning" class="sc-ov">
        <div class="sc-ov__frame">
          <span class="sc-ov__corner sc-ov__corner--tl" />
          <span class="sc-ov__corner sc-ov__corner--tr" />
          <span class="sc-ov__corner sc-ov__corner--bl" />
          <span class="sc-ov__corner sc-ov__corner--br" />
          <div class="sc-ov__laser" />
        </div>
        <div class="sc-ov__hint">Hướng camera vào mã vạch / QR</div>
        <button class="sc-ov__cancel" @click="cancel">Huỷ</button>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { useScannerStore } from '../scanner'
const { scanning, cancel } = useScannerStore()
</script>

<style scoped>
.sc-ov { position: fixed; inset: 0; z-index: 99999; display: flex; flex-direction: column;
  align-items: center; justify-content: center; background: transparent; }
/* khung quét: vùng trong suốt, xung quanh tối nhờ box-shadow lan rộng */
.sc-ov__frame { position: relative; width: 70vw; max-width: 280px; aspect-ratio: 1;
  border-radius: 22px; box-shadow: 0 0 0 100vmax rgba(0,0,0,.45); }
.sc-ov__corner { position: absolute; width: 30px; height: 30px; border: 4px solid #fff; }
.sc-ov__corner--tl { top: -2px; left: -2px; border-right: 0; border-bottom: 0; border-radius: 22px 0 0 0; }
.sc-ov__corner--tr { top: -2px; right: -2px; border-left: 0; border-bottom: 0; border-radius: 0 22px 0 0; }
.sc-ov__corner--bl { bottom: -2px; left: -2px; border-right: 0; border-top: 0; border-radius: 0 0 0 22px; }
.sc-ov__corner--br { bottom: -2px; right: -2px; border-left: 0; border-top: 0; border-radius: 0 0 22px 0; }
.sc-ov__laser { position: absolute; left: 8%; right: 8%; height: 2px; top: 10%;
  background: linear-gradient(90deg, transparent, #2E75B6, transparent); animation: sc-laser 2s ease-in-out infinite; }
@keyframes sc-laser { 0%,100% { top: 10%; } 50% { top: 88%; } }
.sc-ov__hint { color: #fff; margin-top: 28px; font-size: 15px; font-weight: 600; text-shadow: 0 1px 4px rgba(0,0,0,.7); }
.sc-ov__cancel { position: fixed; bottom: calc(30px + env(safe-area-inset-bottom)); left: 50%; transform: translateX(-50%);
  background: #fff; color: #1F4E79; border: none; border-radius: 999px; padding: 13px 34px; font-size: 16px; font-weight: 700;
  box-shadow: 0 4px 18px rgba(0,0,0,.3); }
.sc-ov-enter-active, .sc-ov-leave-active { transition: opacity .2s; }
.sc-ov-enter-from, .sc-ov-leave-to { opacity: 0; }
</style>
