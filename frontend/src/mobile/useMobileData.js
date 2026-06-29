// Tải dữ liệu kiểu stale-while-revalidate cho mobile:
//  - Có cache (sessionStorage) → hiện NGAY, đồng thời refetch nền (mượt, không chớp).
//  - Chưa cache → loading=true.
//  - Tự thử lại 1 lần khi lỗi mạng tạm thời.
// API: const { data, loading, refreshing, error, refresh } = useMobileData(key, fetcher, { immediate })
import { ref, shallowRef, onMounted } from 'vue'

const _isNetErr = (e) => /network|timeout|Failed to fetch|ECONN|tải/i.test(e?.message || '')

export function useMobileData(key, fetcher, { immediate = true } = {}) {
  const data = shallowRef(_readCache(key))
  const loading = ref(data.value == null)   // chỉ "loading" thật khi chưa có gì để hiện
  const refreshing = ref(false)
  const error = ref(null)

  async function run(isRefresh) {
    if (isRefresh) refreshing.value = true
    error.value = null
    try {
      let res
      try { res = await fetcher() }
      catch (e) { if (_isNetErr(e)) { await _sleep(600); res = await fetcher() } else throw e }
      data.value = res
      _writeCache(key, res)
    } catch (e) {
      error.value = e
      if (data.value == null) data.value = null   // giữ nguyên dữ liệu cũ nếu có
    } finally {
      loading.value = false
      refreshing.value = false
    }
  }

  const refresh = () => run(true)
  if (immediate) onMounted(() => run(data.value != null))   // có cache → coi như refresh nền

  return { data, loading, refreshing, error, refresh }
}

function _readCache(key) {
  try { const v = sessionStorage.getItem('mdc:' + key); return v ? JSON.parse(v) : null }
  catch (e) { return null }
}
function _writeCache(key, val) {
  try { sessionStorage.setItem('mdc:' + key, JSON.stringify(val)) } catch (e) {}
}
const _sleep = (ms) => new Promise((r) => setTimeout(r, ms))
