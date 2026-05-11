import { defineStore } from 'pinia'

let _id = 0

export const useToastStore = defineStore('toast', {
  state: () => ({ toasts: [] }),
  actions: {
    push(msg, variant = 'info', timeout = 4000) {
      const id = ++_id
      this.toasts.push({ id, msg, variant })
      if (timeout) setTimeout(() => this.dismiss(id), timeout)
      return id
    },
    success(msg) { return this.push(msg, 'success') },
    warning(msg) { return this.push(msg, 'warning') },
    error(msg)   { return this.push(msg, 'error', 6000) },
    dismiss(id)  { this.toasts = this.toasts.filter(t => t.id !== id) },
  },
})
