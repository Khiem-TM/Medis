import { api } from './axios'
import type {
  HealthBaseline,
  OnboardingStep1Request,
  OnboardingStep2Request,
  OnboardingStep3Request,
  ParsedConditionsResponse,
} from '@/types/onboarding.types'

export const onboardingKeys = {
  all: ['onboarding-status'] as const,
}

export const onboardingApi = {
  getStatus: () => api.get<HealthBaseline>('/users/me/onboarding').then((r) => r.data),
  saveStep1: (data: OnboardingStep1Request) =>
    api.post<HealthBaseline>('/users/me/onboarding/step1', data).then((r) => r.data),
  saveStep2: (data: OnboardingStep2Request) =>
    api.post<HealthBaseline>('/users/me/onboarding/step2', data).then((r) => r.data),
  saveStep3: (data: OnboardingStep3Request) =>
    api.post<HealthBaseline>('/users/me/onboarding/step3', data).then((r) => r.data),
  parseText: (text: string) =>
    api.post<ParsedConditionsResponse>('/users/me/onboarding/parse-text', null, {
      params: { text },
    }).then((r) => r.data),
}
