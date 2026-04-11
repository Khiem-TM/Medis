import { ref } from 'vue'
import { api } from '@/api/axios'
import { downloadBlob } from '@/utils/download'
import { useToast } from './useToast'

export function useExcelExport() {
  const exporting = ref(false)
  const toast = useToast()

  async function exportExcel(url: string, body: unknown, filename: string) {
    exporting.value = true
    try {
      const { data } = await api.post(url, body, { responseType: 'blob' })
      downloadBlob(data, filename)
      toast.success('Xuất file Excel thành công')
    } catch {
      toast.error('Không thể xuất file Excel')
    } finally {
      exporting.value = false
    }
  }

  return { exporting, exportExcel }
}
