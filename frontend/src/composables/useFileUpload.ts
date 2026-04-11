import { ref } from 'vue'

const MAX_SIZE = 2 * 1024 * 1024 // 2MB
const ALLOWED = ['image/jpeg', 'image/png', 'image/webp']

export function useFileUpload() {
  const preview = ref<string | null>(null)
  const file = ref<File | null>(null)
  const error = ref<string | null>(null)

  function onFileChange(e: Event) {
    const input = e.target as HTMLInputElement
    const selected = input.files?.[0]
    error.value = null

    if (!selected) return

    if (!ALLOWED.includes(selected.type)) {
      error.value = 'Chỉ chấp nhận file JPEG, PNG hoặc WebP'
      return
    }

    if (selected.size > MAX_SIZE) {
      error.value = 'File không được vượt quá 2MB'
      return
    }

    file.value = selected
    preview.value = URL.createObjectURL(selected)
  }

  function reset() {
    preview.value = null
    file.value = null
    error.value = null
  }

  return { preview, file, error, onFileChange, reset }
}
