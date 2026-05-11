<script setup>
import { onMounted, ref } from 'vue'
import AppShell from './components/AppShell.vue'
import { getCurrentUser } from './api'

const user = ref('Guest')

onMounted(async () => {
  user.value = await getCurrentUser()
})
</script>

<template>
  <AppShell :user="user">
    <router-view />
  </AppShell>
</template>
