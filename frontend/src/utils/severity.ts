import type { Severity } from '@/types/interaction.types'

export const severityConfig: Record<Severity, { label: string; classes: string }> = {
  minor: {
    label: 'Nhẹ',
    classes: 'bg-yellow-100 text-yellow-800',
  },
  moderate: {
    label: 'Trung bình',
    classes: 'bg-orange-100 text-orange-800',
  },
  major: {
    label: 'Nghiêm trọng',
    classes: 'bg-red-100 text-red-800',
  },
}

export function getSeverityLabel(severity: Severity): string {
  return severityConfig[severity]?.label ?? severity
}

export function getSeverityClasses(severity: Severity): string {
  return severityConfig[severity]?.classes ?? 'bg-gray-100 text-gray-800'
}
