<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { users as usersApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { useAccessStore } from '../stores/access'
import { useToastStore } from '../stores/toast'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import FieldInput from '../components/FieldInput.vue'
import Icon from '../components/Icon.vue'
import Confirm from '../components/Confirm.vue'

const auth = useAuthStore()
const access = useAccessStore()
const toast = useToastStore()
const confirmRef = ref(null)
const router = useRouter()

// L01: chỉ quyết định quyền SAU khi đã biết roles. Access store (access.menu)
// là source of truth (load ở router guard). Tránh hiện banner "cấm" lúc chưa
// boot xong rồi phải F5.
const accessReady = computed(() => access.loaded || auth.booted)
const isAdmin = computed(() => {
  if (access.loaded) {
    if (access.is_admin) return true
    return (access.roles || []).some(r => ['System Manager', 'SupplyCore Manager'].includes(r))
  }
  const r = (auth.user?.roles || []).map(x => x.role || x)
  return r.includes('System Manager') || r.includes('SupplyCore Manager')
})

const roleGuide = ref([])
const userList = ref([])
const loading = ref(false)
const search = ref('')

const editing = ref(null)        // null = closed | {} = create | {name, ...} = edit
const form = ref({ email: '', full_name: '', password: '', password2: '', send_welcome: 1, roles: [] })
const formBusy = ref(false)
const showPw = ref(false)         // hiện/ẩn mật khẩu (dùng chung cho cả 2 ô)

// Chính sách mật khẩu — đồng bộ với backend users._validate_password_strength:
// ≥ 8 ký tự, có chữ HOA + chữ thường + số + ký tự đặc biệt. Để trống = gửi
// email chào mừng (user tự đặt), khi đó bỏ qua kiểm.
const pwChecks = computed(() => {
  const p = form.value.password || ''
  return {
    len: p.length >= 8,
    upper: /[A-Z]/.test(p),
    lower: /[a-z]/.test(p),
    digit: /[0-9]/.test(p),
    special: /[^A-Za-z0-9]/.test(p),
  }
})
const pwStrong = computed(() => Object.values(pwChecks.value).every(Boolean))
const pwMatch = computed(() => (form.value.password || '') === (form.value.password2 || ''))
const pwError = computed(() => {
  if (!form.value.password) return ''                 // để trống → hợp lệ (welcome email)
  if (!pwStrong.value) return 'Mật khẩu chưa đủ mạnh (≥8, hoa, thường, số, ký tự đặc biệt)'
  if (!pwMatch.value) return 'Mật khẩu nhập lại không khớp'
  return ''
})

// === Load ===
async function loadAll() {
  loading.value = true
  try {
    const [g, u] = await Promise.all([
      usersApi.listRoles(),
      usersApi.list(search.value, 200, 1),
    ])
    roleGuide.value = g
    userList.value = u
  } catch (e) {
    toast.error(`Tải danh sách lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadAll, 300)
})

onMounted(async () => {
  // Đợi access store (source of truth) trước khi quyết định quyền & gọi API admin
  if (!access.loaded) { try { await access.load() } catch (e) {} }
  if (isAdmin.value) loadAll()
})

// Nếu access.load() đang chạy từ router guard (load() early-return khi đang
// loading) → onMounted có thể chưa thấy loaded. Khi loaded xong thì nạp danh sách.
watch(() => access.loaded, (v) => {
  if (v && isAdmin.value && !userList.value.length && !loading.value) loadAll()
})

// === Modal ===
function openCreate() {
  editing.value = {}
  showPw.value = false
  form.value = { email: '', full_name: '', password: '', password2: '', send_welcome: 1, roles: [] }
}
function openEdit(u) {
  editing.value = u
  showPw.value = false
  form.value = {
    email: u.email,
    full_name: u.full_name,
    password: '',
    password2: '',
    send_welcome: 0,
    roles: [...u.sc_roles],
  }
}
function closeModal() { editing.value = null }

async function submitForm() {
  // Chặn sớm khi tạo mới có đặt mật khẩu nhưng chưa đạt/không khớp (BE cũng enforce).
  if (!editing.value.name && pwError.value) {
    toast.error(pwError.value)
    return
  }
  formBusy.value = true
  try {
    if (editing.value.name) {
      // Edit roles
      await usersApi.updateRoles(editing.value.name, form.value.roles)
      toast.success(`Đã cập nhật quyền cho ${editing.value.name}`)
    } else {
      await usersApi.create(form.value)
      toast.success(`Đã tạo user ${form.value.email}`)
    }
    closeModal()
    loadAll()
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    formBusy.value = false
  }
}

async function toggleEnabled(u) {
  if (!await confirmRef.value.ask({
    title: u.enabled ? 'Vô hiệu hoá user' : 'Kích hoạt user',
    message: `${u.enabled ? 'Vô hiệu hoá' : 'Kích hoạt'} ${u.name}?`,
    confirmText: u.enabled ? 'Vô hiệu hoá' : 'Kích hoạt',
    variant: u.enabled ? 'danger' : 'primary',
  })) return
  try {
    await usersApi.setEnabled(u.name, !u.enabled)
    toast.success('Đã cập nhật trạng thái')
    loadAll()
  } catch (e) { toast.error(e.message) }
}

async function doReset(u) {
  if (!await confirmRef.value.ask({
    title: 'Reset mật khẩu', message: `Gửi email reset password cho ${u.name}?`, confirmText: 'Gửi email',
  })) return
  try {
    await usersApi.resetPassword(u.name)
    toast.success('Đã gửi email reset password')
  } catch (e) { toast.error(e.message) }
}

async function doDelete(u) {
  if (!await confirmRef.value.ask({
    title: 'Xóa user',
    message: `Xóa vĩnh viễn user ${u.name}? Không thể hoàn tác. `
      + `Nếu user còn ràng buộc dữ liệu (khách hàng Portal, bản ghi liên quan) sẽ bị chặn — khi đó nên Vô hiệu hóa thay vì xóa.`,
    confirmText: 'Xóa', variant: 'danger',
  })) return
  try {
    await usersApi.remove(u.name)
    toast.success(`Đã xóa user ${u.name}`)
    loadAll()
  } catch (e) { toast.error(e.message) }
}

// === Helpers ===
function dangerColor(level) {
  return {
    high: 'bg-sc-danger-50 border-sc-danger/40 text-sc-danger',
    medium: 'bg-sc-warning-50 border-sc-warning/40 text-sc-warning',
    low: 'bg-sc-success-50 border-sc-success/40 text-sc-success',
  }[level] || 'bg-slate-50 border-slate-300'
}
function dangerDot(level) {
  return {
    high: 'bg-sc-danger',
    medium: 'bg-sc-warning',
    low: 'bg-sc-success',
  }[level] || 'bg-slate-400'
}

function isRoleTicked(role) {
  return form.value.roles.includes(role)
}
function toggleRole(role) {
  const i = form.value.roles.indexOf(role)
  if (i >= 0) form.value.roles.splice(i, 1)
  else form.value.roles.push(role)
}

const tickedRoleInfo = computed(() =>
  roleGuide.value.filter(g => form.value.roles.includes(g.role)))
</script>

<template>
  <div v-if="!accessReady" class="sc-card p-10 text-center text-sc-text-muted">
    <div class="text-4xl mb-3 animate-spin inline-block"><Icon name="rotate-cw" :size="40" /></div>
    Đang kiểm tra quyền…
  </div>

  <div v-else-if="!isAdmin" class="sc-card p-10 text-center">
    <div class="text-4xl mb-3"><Icon name="shield" :size="40" /></div>
    <h2 class="text-lg font-bold text-sc-navy mb-2">Cần quyền quản lý user</h2>
    <p class="text-sm text-sc-text-muted">
      Chỉ <b>System Manager</b> hoặc <b>SupplyCore Manager</b> mới truy cập được trang này.
    </p>
  </div>

  <div v-else>
    <PageHeader title="Người dùng & Phân quyền" icon="users"
      code="User Management · RBAC"
      :subtitle="`${userList.length} user SupplyCore — ${roleGuide.length} role có hướng dẫn`">
      <template #actions>
        <button @click="loadAll" class="sc-btn-secondary text-sm" title="Tải lại">
          <Icon name="rotate-cw" :size="14" />
        </button>
        <button @click="openCreate" class="sc-btn-primary text-sm">+ Tạo user</button>
      </template>
    </PageHeader>

    <!-- Search + filter -->
    <div class="sc-card p-3 mb-4 flex items-center gap-3">
      <FieldInput v-model="search" placeholder="Tìm theo email / tên..."
        prefix-icon="search"
        class="flex-1 max-w-md" />
    </div>

    <!-- User table -->
    <div class="sc-card overflow-hidden">
      <div class="overflow-x-auto">
      <table class="sc-table">
        <thead class="bg-sc-bg">
          <tr>
            <th class="px-4 py-2 text-left text-xs font-medium text-sc-text-muted">Email / Username</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-sc-text-muted">Họ tên</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-sc-text-muted">SupplyCore Roles</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-sc-text-muted">Trạng thái</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-sc-text-muted">Đăng nhập gần nhất</th>
            <th class="px-4 py-2 text-right text-xs font-medium text-sc-text-muted">Thao tác</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-sc-border">
          <tr v-if="loading">
            <td colspan="6" class="px-4 py-6 text-center text-sc-text-muted">Đang tải…</td>
          </tr>
          <tr v-else-if="!userList.length">
            <td colspan="6" class="px-4 py-6 text-center text-sc-text-muted">Không có user nào</td>
          </tr>
          <tr v-for="u in userList" :key="u.name" class="hover:bg-sc-bg">
            <td class="px-4 py-2 font-mono text-xs">{{ u.name }}</td>
            <td class="px-4 py-2">{{ u.full_name || '—' }}</td>
            <td class="px-4 py-2">
              <div class="flex flex-wrap gap-1">
                <span v-for="r in u.sc_roles" :key="r"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-sc-royal/10 text-sc-royal font-medium">
                  {{ r.replace(/^SupplyCore /, '') }}
                </span>
                <span v-if="!u.sc_roles.length" class="text-xs text-sc-text-muted">—</span>
              </div>
            </td>
            <td class="px-4 py-2">
              <span class="sc-badge"
                :class="u.enabled ? 'sc-badge-success' : 'sc-badge-neutral'">
                {{ u.enabled ? 'Bật' : 'Tắt' }}
              </span>
            </td>
            <td class="px-4 py-2 text-xs text-sc-text-muted">
              {{ u.last_login || '—' }}
            </td>
            <td class="px-4 py-2 text-right whitespace-nowrap">
              <button @click="openEdit(u)" class="sc-btn-secondary text-xs">Sửa quyền</button>
              <button @click="doReset(u)" class="sc-btn-secondary text-xs ml-1"
                :disabled="u.name === 'Administrator'" title="Gửi email reset">
                <Icon name="mail" :size="14" />
              </button>
              <button @click="toggleEnabled(u)" class="sc-btn-secondary text-xs ml-1"
                :disabled="u.name === 'Administrator'">
                <Icon :name="u.enabled ? 'ban' : 'play'" :size="14" />
                {{ u.enabled ? 'Tắt' : 'Bật' }}
              </button>
              <button v-if="u.name !== 'Administrator' && u.name !== access.user"
                @click="doDelete(u)"
                class="sc-btn-secondary text-xs ml-1 text-sc-danger hover:!bg-sc-danger hover:!text-white"
                title="Xóa user (không hồi phục)">
                <Icon name="trash-2" :size="14" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- Role legend (compact) -->
    <details class="sc-card mt-5 p-4">
      <summary class="cursor-pointer text-sm font-medium text-sc-navy">
        <Icon name="book" :size="16" /> Danh mục role + chức năng / giới hạn
      </summary>
      <div class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
        <div v-for="r in roleGuide" :key="r.role"
          class="border rounded-lg p-3" :class="dangerColor(r.danger_level)">
          <div class="flex items-start gap-2">
            <span class="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" :class="dangerDot(r.danger_level)"></span>
            <div class="flex-1 min-w-0">
              <div class="font-semibold text-sm">{{ r.role }}</div>
              <div class="text-xs opacity-80">{{ r.vn_name }} · {{ r.scope }}</div>
              <div class="mt-1 text-xs">
                <b>Modules:</b> {{ r.modules.join(', ') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </details>

    <!-- =================== Modal: Create / Edit =================== -->
    <Modal :open="editing !== null" size="xl"
      :title="editing?.name ? `Phân quyền: ${editing.name}` : 'Tạo user mới'"
      @close="closeModal">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <!-- LEFT: form -->
        <div class="space-y-3">
          <div v-if="!editing?.name">
            <label class="text-xs font-medium text-sc-text-muted block mb-1">
              Email <span class="text-sc-danger">*</span>
            </label>
            <input v-model="form.email" type="email" class="sc-input w-full"
              placeholder="ten.nv@miyano.com.vn" />
          </div>
          <div v-else class="text-sm">
            <b>{{ editing.name }}</b>
            <span class="text-xs text-sc-text-muted ml-2">(không sửa được email)</span>
          </div>

          <div>
            <label class="text-xs font-medium text-sc-text-muted block mb-1">Họ tên</label>
            <input v-model="form.full_name" type="text" class="sc-input w-full"
              :placeholder="editing?.name ? editing.full_name : 'Nguyễn Văn A'"
              :disabled="!!editing?.name" />
          </div>

          <div v-if="!editing?.name" class="space-y-2">
            <div>
              <label class="text-xs font-medium text-sc-text-muted block mb-1">
                Mật khẩu khởi tạo
                <span class="text-sc-text-muted/70">(để trống → gửi email chào mừng để user tự đặt)</span>
              </label>
              <div class="relative">
                <input v-model="form.password" :type="showPw ? 'text' : 'password'"
                  class="sc-input w-full pr-10" autocomplete="new-password"
                  placeholder="Tối thiểu 8 ký tự, hoặc để trống" />
                <button type="button" @click="showPw = !showPw" tabindex="-1"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-sc-text-muted hover:text-sc-text"
                  :title="showPw ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'">
                  <Icon :name="showPw ? 'eye-off' : 'eye'" :size="16" />
                </button>
              </div>
            </div>

            <div v-if="form.password">
              <label class="text-xs font-medium text-sc-text-muted block mb-1">
                Nhập lại mật khẩu <span class="text-sc-danger">*</span>
              </label>
              <input v-model="form.password2" :type="showPw ? 'text' : 'password'"
                class="sc-input w-full" autocomplete="new-password"
                :class="form.password2 && !pwMatch ? 'border-sc-danger' : ''"
                placeholder="Gõ lại đúng mật khẩu trên" />
            </div>

            <!-- Checklist quy định ký tự — chỉ hiện khi có nhập mật khẩu -->
            <ul v-if="form.password" class="text-xs space-y-0.5 mt-1 pl-1">
              <li :class="pwChecks.len ? 'text-sc-success' : 'text-sc-text-muted'">
                {{ pwChecks.len ? '✓' : '•' }} Ít nhất 8 ký tự</li>
              <li :class="pwChecks.upper && pwChecks.lower ? 'text-sc-success' : 'text-sc-text-muted'">
                {{ pwChecks.upper && pwChecks.lower ? '✓' : '•' }} Có chữ in HOA và chữ thường</li>
              <li :class="pwChecks.digit ? 'text-sc-success' : 'text-sc-text-muted'">
                {{ pwChecks.digit ? '✓' : '•' }} Có chữ số</li>
              <li :class="pwChecks.special ? 'text-sc-success' : 'text-sc-text-muted'">
                {{ pwChecks.special ? '✓' : '•' }} Có ký tự đặc biệt (@ # ! $ %…)</li>
              <li v-if="form.password2" :class="pwMatch ? 'text-sc-success' : 'text-sc-danger'">
                {{ pwMatch ? '✓' : '✕' }} Nhập lại khớp</li>
            </ul>

            <label class="flex items-center gap-2 mt-2 text-sm">
              <input type="checkbox" v-model="form.send_welcome" :true-value="1" :false-value="0" />
              Gửi email chào mừng (kèm link đặt mật khẩu)
            </label>
          </div>

          <hr class="border-sc-border" />

          <!-- LEGEND of ticked roles -->
          <div>
            <h4 class="text-sm font-semibold text-sc-navy mb-2">
              <Icon name="shield" :size="16" /> Giải thích quyền đang chọn ({{ tickedRoleInfo.length }})
            </h4>
            <div v-if="!tickedRoleInfo.length" class="text-xs text-sc-text-muted italic
              border border-dashed border-sc-border rounded-lg p-4 text-center">
              Tick vào role bên phải để xem chức năng + giới hạn ở đây
            </div>
            <div v-else class="space-y-3 max-h-[400px] overflow-y-auto">
              <div v-for="r in tickedRoleInfo" :key="r.role"
                class="border rounded-lg p-3" :class="dangerColor(r.danger_level)">
                <div class="flex items-center gap-2 mb-2">
                  <span class="w-2 h-2 rounded-full" :class="dangerDot(r.danger_level)"></span>
                  <span class="font-semibold text-sm">{{ r.role }}</span>
                  <span v-if="r.danger_level === 'high'"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-sc-danger-50 text-sc-danger font-bold">
                    <Icon name="alert-triangle" :size="12" /> SIÊU QUYỀN
                  </span>
                </div>
                <div class="text-xs mb-1"><b>{{ r.vn_name }}</b></div>
                <div class="text-xs mb-2 opacity-80"><b>Phạm vi:</b> {{ r.scope }}</div>
                <div class="text-xs mb-2">
                  <div class="font-medium mb-0.5"><Icon name="check-circle" :size="14" /> Chức năng:</div>
                  <ul class="list-disc list-inside space-y-0.5 opacity-90">
                    <li v-for="(d, i) in r.duties" :key="i">{{ d }}</li>
                  </ul>
                </div>
                <div class="text-xs">
                  <div class="font-medium mb-0.5"><Icon name="ban" :size="14" /> Giới hạn:</div>
                  <ul class="list-disc list-inside space-y-0.5 opacity-90">
                    <li v-for="(l, i) in r.limits" :key="i">{{ l }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: role checkboxes -->
        <div>
          <h4 class="text-sm font-semibold text-sc-navy mb-2">
            Tick role để gán ({{ form.roles.length }} đã chọn)
          </h4>
          <p class="text-xs text-sc-text-muted mb-3">
            Mỗi role có chức năng + giới hạn riêng — xem giải thích bên trái sau khi tick.
            User có thể có <i>nhiều</i> role; quyền là <b>hợp</b> của tất cả role.
          </p>
          <div class="space-y-1.5 max-h-[480px] overflow-y-auto pr-1">
            <label v-for="r in roleGuide" :key="r.role"
              class="flex items-start gap-3 p-2.5 border rounded-lg cursor-pointer hover:bg-sc-bg transition"
              :class="isRoleTicked(r.role) ? 'border-sc-royal bg-sc-royal/5' : 'border-sc-border'">
              <input type="checkbox" :checked="isRoleTicked(r.role)"
                @change="toggleRole(r.role)" class="mt-1 flex-shrink-0" />
              <span class="w-2 h-2 rounded-full mt-2 flex-shrink-0" :class="dangerDot(r.danger_level)"></span>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-sc-text">
                  {{ r.role }}
                  <span v-if="r.danger_level === 'high'"
                    class="text-[9px] px-1 py-0.5 rounded bg-sc-danger-50 text-sc-danger font-bold ml-1"><Icon name="alert-triangle" :size="11" /> TỐI CAO</span>
                </div>
                <div class="text-xs text-sc-text-muted">{{ r.vn_name }}</div>
                <div class="text-[10px] text-sc-text-muted font-mono mt-0.5">
                  {{ r.modules.join(' · ') }}
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      <template #footer>
        <button @click="closeModal" class="sc-btn-secondary text-sm" :disabled="formBusy">
          Huỷ
        </button>
        <button @click="submitForm" class="sc-btn-primary text-sm"
          :disabled="formBusy || !!pwError" :title="pwError || ''">
          <Icon v-if="!formBusy && editing?.name" name="save" :size="14" />
          {{ formBusy ? 'Đang lưu…' : (editing?.name ? 'Lưu phân quyền' : '+ Tạo user') }}
        </button>
      </template>
    </Modal>

    <Confirm ref="confirmRef" />
  </div>
</template>
