import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { onboardingApi } from '@/api/onboarding.api'
import type {
  HealthBaseline,
  OnboardingStep1Request,
  OnboardingStep2Request,
  OnboardingStep3Request,
} from '@/types/onboarding.types'

export const useOnboardingStore = defineStore('onboarding', () => {
  const status = ref<HealthBaseline | null>(null)
  const loading = ref(false)

  const currentStep = computed(() => {
    if (!status.value) return 1
    if (status.value.onboarding_completed) return 3
    return Math.max(1, status.value.onboarding_step + 1)
  })

  async function loadStatus(force = false) {
    if (status.value && !force) return status.value
    loading.value = true
    try {
      status.value = await onboardingApi.getStatus()
      return status.value
    } finally {
      loading.value = false
    }
  }

  async function saveStep1(data: OnboardingStep1Request) {
    status.value = await onboardingApi.saveStep1(data)
    return status.value
  }

  async function saveStep2(data: OnboardingStep2Request) {
    status.value = await onboardingApi.saveStep2(data)
    return status.value
  }

  async function saveStep3(data: OnboardingStep3Request) {
    status.value = await onboardingApi.saveStep3(data)
    return status.value
  }

  async function complete(data: OnboardingStep3Request) {
    return saveStep3(data)
  }

  function clear() {
    status.value = null
  }

  return {
    status,
    loading,
    currentStep,
    loadStatus,
    saveStep1,
    saveStep2,
    saveStep3,
    complete,
    clear,
  }
})
