import { ref } from 'vue'
import type { ApiError } from '../types/api'

/** 统一异步态：loading / error / 结果，错误可恢复（retry 交给调用方）。 */
export function useAsync<T>(task: () => Promise<T>) {
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const data = ref<T | null>(null)

  async function run(): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await task()
      data.value = result
      return result
    } catch (caught) {
      error.value = caught as ApiError
      return null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    error.value = null
    data.value = null
  }

  return { loading, error, data, run, reset }
}
