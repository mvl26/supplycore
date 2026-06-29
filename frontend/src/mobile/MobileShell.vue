<!-- frontend/src/mobile/MobileShell.vue -->
<template>
  <div class="m-shell">
    <main class="m-content"><router-view /></main>
    <nav class="m-tabbar">
      <router-link
        v-for="t in tabs"
        :key="t.to"
        :to="t.to"
        class="m-tab"
        active-class="m-tab--active"
      >
        <Icon :name="t.icon" :size="22" />
        <span>{{ t.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import Icon from '../components/Icon.vue'

const tabs = [
  { to: '/m/lookup',    icon: 'layers',          label: 'Tra cứu'   },
  { to: '/m/approve',   icon: 'clipboard-check', label: 'Duyệt'     },
  { to: '/m/receiving', icon: 'truck',            label: 'Tiếp nhận' },
  { to: '/m/dashboard', icon: 'bar-chart',        label: 'Bảng tin'  },
]
</script>

<style scoped>
.m-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.m-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  padding-bottom: 72px;
}
.m-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  display: flex;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}
.m-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 11px;
  color: #6b7280;
  text-decoration: none;
}
.m-tab--active {
  color: #1F4E79;
}
</style>
