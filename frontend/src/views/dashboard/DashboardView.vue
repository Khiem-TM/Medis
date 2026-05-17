<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStats } from '@/api/admin.api'
import { useIntakeStats, useIntakesByDate } from '@/api/intakes.api'
import { useTodaySchedule, useConfirmIntakeMutation } from '@/api/reminders.api'
import { useLatestVital, useCreateVitalMutation } from '@/api/vitals.api'
import { useAuthStore } from '@/stores/auth.store'

const router = useRouter()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || 'Bạn')

// ── Date navigation ──────────────────────────────────────────────────────────
function toISO(d: Date) {
  return d.toISOString().slice(0, 10)
}
const today = toISO(new Date())
const scheduleDate = ref<string>(today)
const isToday = computed(() => scheduleDate.value === today)

function shiftDate(days: number) {
  const d = new Date(scheduleDate.value)
  d.setDate(d.getDate() + days)
  scheduleDate.value = toISO(d)
}
function goToday() { scheduleDate.value = today }

function formatScheduleDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}

// ── Data queries ─────────────────────────────────────────────────────────────
const { data: adminStats } = useAdminStats(isAdmin)
const { data: reminders, isLoading: loadingReminders } = useTodaySchedule(scheduleDate)
const { data: intakeLogs, isLoading: loadingLogs } = useIntakesByDate(scheduleDate)
const { data: todayStats, isLoading: loadingTodayStats } = useIntakeStats(ref('today'))
const { data: weekStats } = useIntakeStats(ref('week'))
const { data: monthStats } = useIntakeStats(ref('month'))
const { data: latestVital, isLoading: loadingVitals } = useLatestVital()

// ── Mutations ────────────────────────────────────────────────────────────────
const confirmMutation = useConfirmIntakeMutation()
const createVitalMutation = useCreateVitalMutation()

// ── Schedule helpers ─────────────────────────────────────────────────────────
const intakeMap = computed(() => {
  const map = new Map<number, { status: string; taken_at: string | null }>()
  for (const log of intakeLogs.value ?? []) {
    if (log.reminder_id != null) map.set(log.reminder_id, { status: log.status, taken_at: log.taken_at ?? null })
  }
  return map
})

function getDoseStatus(reminderId: number) {
  return intakeMap.value.get(reminderId)?.status ?? 'pending'
}

function markTaken(reminderId: number) {
  if (!isToday.value) return
  confirmMutation.mutate({ reminderId })
}

// ── Hero: next upcoming reminder ─────────────────────────────────────────────
const now = new Date()
const nowMinutes = now.getHours() * 60 + now.getMinutes()

const nextReminder = computed(() => {
  if (!isToday.value) return null
  return (reminders.value ?? []).find((r) => {
    const [h, m] = r.reminder_time.split(':').map(Number)
    const rMins = h * 60 + m
    const status = getDoseStatus(r.id)
    return rMins > nowMinutes && status === 'pending'
  }) ?? null
})

const minutesToNext = computed(() => {
  if (!nextReminder.value) return 0
  const [h, m] = nextReminder.value.reminder_time.split(':').map(Number)
  return h * 60 + m - nowMinutes
})

// ── Today's progress ─────────────────────────────────────────────────────────
const todayTotal = computed(() => todayStats.value?.total_scheduled ?? (reminders.value?.length ?? 0))
const todayDone = computed(() => todayStats.value?.total_taken ?? 0)
const ringPct = computed(() => todayTotal.value > 0 ? todayDone.value / todayTotal.value : 0)

// ── Vitals form ───────────────────────────────────────────────────────────────
const showVitalsForm = ref(false)
const vitalsForm = ref({ heart_rate: '', systolic_bp: '', diastolic_bp: '', blood_glucose: '' })

function submitVitals() {
  createVitalMutation.mutate({
    heart_rate: vitalsForm.value.heart_rate ? Number(vitalsForm.value.heart_rate) : null,
    systolic_bp: vitalsForm.value.systolic_bp ? Number(vitalsForm.value.systolic_bp) : null,
    diastolic_bp: vitalsForm.value.diastolic_bp ? Number(vitalsForm.value.diastolic_bp) : null,
    blood_glucose: vitalsForm.value.blood_glucose ? Number(vitalsForm.value.blood_glucose) : null,
  }, {
    onSuccess: () => {
      showVitalsForm.value = false
      vitalsForm.value = { heart_rate: '', systolic_bp: '', diastolic_bp: '', blood_glucose: '' }
    },
  })
}

// ── Timeline ruler helpers ────────────────────────────────────────────────────
const NOW_PCT = computed(() => Math.min(100, Math.max(0, ((nowMinutes / 60 - 6) / 18) * 100)))

function reminderPct(time: string) {
  const [h, m] = time.split(':').map(Number)
  return Math.min(100, Math.max(0, ((h + m / 60 - 6) / 18) * 100))
}

// ── Quick actions ─────────────────────────────────────────────────────────────
const quickActions = [
  { id: 'ai', label: 'Hỏi AI', sub: 'Tư vấn triệu chứng & thuốc', path: '/chatbot', color: '#7C3AED', bg: '#EDE9FE',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
  { id: 'add', label: 'Thêm đơn thuốc', sub: 'Nhập thủ công hoặc ảnh đơn', path: '/profile/prescriptions', color: '#2563EB', bg: '#DCEDFF',
    icon: 'M12 4v16m8-8H4' },
  { id: 'check', label: 'Tra cứu tương tác', sub: 'Kiểm tra 2–20 thuốc', path: '/interactions', color: '#059669', bg: '#D1FAE5',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
  { id: 'find', label: 'Tra cứu thuốc', sub: 'Tìm theo tên / hoạt chất', path: '/drugs', color: '#0C1D42', bg: '#EFF3F8',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
]

// ── Status badge helpers ──────────────────────────────────────────────────────
function statusLabel(status: string, isNext: boolean) {
  if (status === 'taken' || status === 'late') return 'Đã uống'
  if (isNext) return 'Sắp tới'
  return 'Chờ'
}
function statusStyle(status: string, isNext: boolean) {
  if (status === 'taken' || status === 'late') return 'background:#D1FAE5;color:#065F46;'
  if (isNext) return 'background:#DCEDFF;color:#1D4FD8;'
  return 'background:#F3F5F7;color:#8A95AC;'
}
function toneColor(index: number) {
  const colors = ['#2563EB', '#059669', '#F59E0B', '#7C3AED', '#EF4444', '#0891B2']
  return colors[index % colors.length]
}
function toneBg(index: number) {
  const bgs = ['#DCEDFF', '#D1FAE5', '#FEF3C7', '#EDE9FE', '#FEE2E2', '#CFFAFE']
  return bgs[index % bgs.length]
}
</script>

<template>
  <div class="dash-root">

    <!-- ══ ROW 1: Hero + Stats ══════════════════════════════════════════════ -->
    <div class="dash-row1">

      <!-- Hero: next dose countdown -->
      <section class="dash-hero">
        <div class="dash-hero-bg" aria-hidden="true">
          <svg viewBox="0 0 800 260" preserveAspectRatio="none" style="position:absolute;inset:0;width:100%;height:100%;">
            <defs>
              <radialGradient id="hg1" cx="15%" cy="110%" r="90%">
                <stop offset="0" stop-color="rgba(255,255,255,.14)"/>
                <stop offset="1" stop-color="rgba(255,255,255,0)"/>
              </radialGradient>
              <radialGradient id="hg2" cx="100%" cy="0%" r="80%">
                <stop offset="0" stop-color="rgba(220,237,255,.35)"/>
                <stop offset="1" stop-color="rgba(220,237,255,0)"/>
              </radialGradient>
            </defs>
            <rect width="800" height="260" fill="url(#hg1)"/>
            <rect width="800" height="260" fill="url(#hg2)"/>
            <circle cx="700" cy="30" r="140" fill="rgba(255,255,255,.045)"/>
            <circle cx="50" cy="230" r="90" fill="rgba(255,255,255,.03)"/>
          </svg>
        </div>

        <div class="dash-hero-inner">
          <div class="dash-hero-left">
            <div class="dash-hero-tag">
              <span class="dash-pulse"></span>
              LIỀU TIẾP THEO · Next dose
            </div>

            <!-- No upcoming reminder -->
            <template v-if="!nextReminder">
              <div class="dash-hero-counter">
                <div class="dash-hero-time">
                  <span class="dash-hero-time-num">—</span>
                  <span class="dash-hero-time-meta">
                    {{ !isToday ? 'Xem lịch sử' : todayDone > 0 ? 'Tất cả đã uống hôm nay 🎉' : 'Chưa có lịch' }}
                  </span>
                </div>
              </div>
            </template>

            <!-- Has next reminder -->
            <template v-else>
              <div class="dash-hero-counter">
                <div class="dash-hero-time">
                  <span class="dash-hero-time-num">{{ nextReminder.reminder_time }}</span>
                  <span class="dash-hero-time-meta">
                    trong <b>{{ minutesToNext }} phút</b>
                  </span>
                </div>
                <div class="dash-hero-divider"></div>
                <div class="dash-hero-drug">
                  <div class="dash-hero-drug-name">{{ nextReminder.drug_name }}</div>
                  <div class="dash-hero-drug-meta">{{ nextReminder.notes ?? nextReminder.frequency }}</div>
                </div>
              </div>
              <div class="dash-hero-actions">
                <button
                  class="dash-btn-primary"
                  :disabled="confirmMutation.isPending.value"
                  @click="markTaken(nextReminder!.id)"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Đã uống · Mark as taken
                </button>
                <button class="dash-btn-ghost">Hoãn 15 phút</button>
                <button class="dash-btn-ghost">Bỏ qua</button>
              </div>
            </template>
          </div>

          <!-- Hero aside -->
          <div class="dash-hero-aside">
            <div class="dash-hero-pill-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" class="w-8 h-8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
              </svg>
            </div>
            <div class="dash-hero-aside-meta">
              <div class="dash-hero-aside-label">Chào mừng</div>
              <div class="dash-hero-aside-val">{{ userName }}</div>
              <div class="dash-hero-aside-sub">
                {{ isAdmin ? 'Admin · Quản trị viên' : 'Theo dõi sức khoẻ hằng ngày' }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Stats ring card -->
      <aside class="dash-stats-card">
        <div class="dash-stats-head">
          <div class="dash-stats-eyebrow">Hôm nay</div>
          <template v-if="isAdmin && adminStats">
            <div class="dash-stats-admin">
              <span>{{ adminStats.total_users.toLocaleString() }} users</span>
              <span>{{ adminStats.total_drugs.toLocaleString() }} thuốc</span>
            </div>
          </template>
        </div>

        <div class="dash-stats-ring-wrap">
          <svg viewBox="0 0 120 120" class="dash-ring-svg">
            <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(12,29,66,.07)" stroke-width="10"/>
            <circle
              cx="60" cy="60" r="50" fill="none"
              stroke="#2563EB" stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="`${ringPct * 314} 314`"
              transform="rotate(-90 60 60)"
            />
          </svg>
          <div class="dash-ring-center">
            <div class="dash-ring-num">
              {{ loadingTodayStats ? '—' : todayDone }}<span>/{{ loadingTodayStats ? '—' : todayTotal }}</span>
            </div>
            <div class="dash-ring-lbl">liều đã uống</div>
          </div>
        </div>

        <div class="dash-stats-bars">
          <div class="dash-stat-bar">
            <span>Tuân thủ tuần</span>
            <div class="dash-bar-track">
              <i :style="`width:${weekStats ? Math.round(weekStats.adherence_rate * 100) : 0}%`"></i>
            </div>
            <b>{{ weekStats ? Math.round(weekStats.adherence_rate * 100) + '%' : '—' }}</b>
          </div>
          <div class="dash-stat-bar">
            <span>Tháng này</span>
            <div class="dash-bar-track">
              <i :style="`width:${monthStats ? Math.round(monthStats.adherence_rate * 100) : 0}%; background:#10B981;`"></i>
            </div>
            <b>{{ monthStats ? Math.round(monthStats.adherence_rate * 100) + '%' : '—' }}</b>
          </div>
        </div>
      </aside>
    </div>

    <!-- ══ ROW 2: Quick actions ═══════════════════════════════════════════════ -->
    <div class="dash-qa">
      <button
        v-for="a in quickActions"
        :key="a.id"
        class="dash-qa-tile"
        @click="router.push(a.path)"
      >
        <span class="dash-qa-icon" :style="`background:${a.bg};`">
          <svg class="w-[18px] h-[18px]" :style="`color:${a.color};`" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" :d="a.icon"/>
          </svg>
        </span>
        <span class="dash-qa-text">
          <b>{{ a.label }}</b>
          <em>{{ a.sub }}</em>
        </span>
        <svg class="dash-qa-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

    <!-- ══ ROW 3: Schedule + Side panels ═════════════════════════════════════ -->
    <div class="dash-row3">

      <!-- Schedule card -->
      <section class="dash-card dash-schedule">
        <header class="dash-card-h">
          <div>
            <div class="dash-eyebrow">Lịch uống thuốc · Schedule</div>
            <h2 class="dash-card-title">{{ formatScheduleDate(scheduleDate) }}</h2>
          </div>
          <div class="dash-card-actions">
            <button class="dash-tab-btn" :class="{ 'is-on': isToday }" @click="goToday">Hôm nay</button>
            <button class="dash-date-nav" @click="shiftDate(-1)">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
            </button>
            <input
              type="date"
              class="dash-date-input"
              :value="scheduleDate"
              @change="scheduleDate = ($event.target as HTMLInputElement).value"
            />
            <button class="dash-date-nav" @click="shiftDate(1)" :disabled="isToday">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
            </button>
          </div>
        </header>

        <!-- Time ruler -->
        <div class="dash-timeline">
          <div
            v-for="h in [6, 9, 12, 15, 18, 21, 24]"
            :key="h"
            class="dash-tick"
            :style="`left: ${((h - 6) / 18) * 100}%`"
          >
            <span>{{ String(h).padStart(2,'0') }}:00</span>
          </div>
          <!-- "now" marker -->
          <div v-if="isToday" class="dash-now-marker" :style="`left: ${NOW_PCT}%`">
            <span class="dash-now-dot"></span>
            <span class="dash-now-lbl">{{ `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}` }}</span>
          </div>
          <!-- Dose blips on ruler -->
          <div
            v-for="r in (reminders ?? [])"
            :key="r.id"
            class="dash-blip"
            :style="`left: ${reminderPct(r.reminder_time)}%; background: ${toneColor(reminders!.indexOf(r))};`"
            :title="r.drug_name"
          ></div>
        </div>

        <!-- Dose list -->
        <div v-if="loadingReminders || loadingLogs" class="dash-loading">
          <div v-for="i in 3" :key="i" class="dash-skeleton"></div>
        </div>
        <div v-else-if="!reminders?.length" class="dash-empty">
          <svg class="w-10 h-10 mx-auto mb-3" style="color:#B5BCCB;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
          </svg>
          <p style="color:#5A6985;font-weight:600;">Không có lịch uống thuốc ngày này</p>
          <p style="color:#8A95AC;font-size:13px;margin-top:4px;">Tạo nhắc nhở để theo dõi</p>
        </div>
        <ul v-else class="dash-dose-list">
          <li
            v-for="(r, idx) in reminders"
            :key="r.id"
            class="dash-dose"
            :class="{
              'is-done': ['taken','late'].includes(getDoseStatus(r.id)),
              'is-next': r.id === nextReminder?.id
            }"
          >
            <!-- Check button -->
            <button
              v-if="isToday"
              class="dash-check-btn"
              :disabled="['taken','late'].includes(getDoseStatus(r.id)) || confirmMutation.isPending.value"
              :style="`border-color:${['taken','late'].includes(getDoseStatus(r.id)) ? toneColor(idx) : 'rgba(12,29,66,.15)'};
                background:${['taken','late'].includes(getDoseStatus(r.id)) ? toneColor(idx) : 'transparent'};`"
              @click="markTaken(r.id)"
            >
              <svg v-if="['taken','late'].includes(getDoseStatus(r.id))" class="w-3 h-3" style="color:white;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
            </button>
            <div v-else class="dash-check-btn" style="border-color:rgba(12,29,66,.1);cursor:default;"></div>

            <!-- Time -->
            <div class="dash-dose-time">
              <span class="dash-dose-time-num">{{ r.reminder_time }}</span>
            </div>

            <!-- Pill icon -->
            <div class="dash-dose-pill-icon" :style="`background:${toneBg(idx)};`">
              <svg class="w-4 h-4" :style="`color:${toneColor(idx)};`" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
              </svg>
            </div>

            <!-- Info -->
            <div class="dash-dose-body">
              <div class="dash-dose-drug">{{ r.drug_name }}</div>
              <div class="dash-dose-meta">{{ r.frequency }} <span v-if="r.notes" class="dash-dose-tag">· {{ r.notes }}</span></div>
            </div>

            <!-- Status badge -->
            <span class="dash-status-badge" :style="statusStyle(getDoseStatus(r.id), r.id === nextReminder?.id)">
              <span v-if="r.id === nextReminder?.id && getDoseStatus(r.id) === 'pending'" class="dash-pulse-sm"></span>
              {{ statusLabel(getDoseStatus(r.id), r.id === nextReminder?.id) }}
            </span>
          </li>
        </ul>
      </section>

      <!-- Side panels -->
      <div class="dash-side-panels">

        <!-- Vitals card -->
        <section class="dash-card dash-vitals-card">
          <header class="dash-card-h">
            <div>
              <div class="dash-eyebrow">Theo dõi · Vitals</div>
              <h3 class="dash-card-title-sm">Chỉ số sức khoẻ</h3>
            </div>
            <button class="dash-link" @click="showVitalsForm = !showVitalsForm">
              {{ showVitalsForm ? 'Huỷ' : 'Cập nhật' }}
            </button>
          </header>

          <!-- Vitals form -->
          <form v-if="showVitalsForm" class="dash-vitals-form" @submit.prevent="submitVitals">
            <div class="dash-vitals-form-row">
              <label>Nhịp tim (bpm)</label>
              <input type="number" v-model="vitalsForm.heart_rate" placeholder="72" min="30" max="250"/>
            </div>
            <div class="dash-vitals-form-row">
              <label>Huyết áp tâm thu (mmHg)</label>
              <input type="number" v-model="vitalsForm.systolic_bp" placeholder="120" min="60" max="250"/>
            </div>
            <div class="dash-vitals-form-row">
              <label>Huyết áp tâm trương (mmHg)</label>
              <input type="number" v-model="vitalsForm.diastolic_bp" placeholder="80" min="40" max="150"/>
            </div>
            <div class="dash-vitals-form-row">
              <label>Đường huyết (mmol/L)</label>
              <input type="number" step="0.1" v-model="vitalsForm.blood_glucose" placeholder="5.4" min="1" max="30"/>
            </div>
            <button type="submit" class="dash-btn-primary-sm" :disabled="createVitalMutation.isPending.value">
              {{ createVitalMutation.isPending.value ? 'Đang lưu...' : 'Lưu chỉ số' }}
            </button>
          </form>

          <!-- Vitals display -->
          <template v-else>
            <div v-if="loadingVitals" class="dash-vitals-list">
              <div v-for="i in 3" :key="i" class="dash-skeleton" style="height:42px;"></div>
            </div>
            <div v-else-if="!latestVital" class="dash-empty-sm">
              <p>Chưa có dữ liệu chỉ số</p>
              <button class="dash-link" @click="showVitalsForm = true">Thêm chỉ số ngay</button>
            </div>
            <ul v-else class="dash-vitals-list">
              <li v-if="latestVital.heart_rate" class="dash-vital-row" style="--vc:#EF4444;--vbg:#FEE2E2;">
                <span class="dash-vital-icon">
                  <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </span>
                <div class="dash-vital-meta">
                  <div class="dash-vital-label">Nhịp tim</div>
                  <div class="dash-vital-val">{{ latestVital.heart_rate }}<span>bpm</span></div>
                </div>
              </li>
              <li v-if="latestVital.systolic_bp && latestVital.diastolic_bp" class="dash-vital-row" style="--vc:#2563EB;--vbg:#DCEDFF;">
                <span class="dash-vital-icon">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
                </span>
                <div class="dash-vital-meta">
                  <div class="dash-vital-label">Huyết áp</div>
                  <div class="dash-vital-val">{{ latestVital.systolic_bp }}/{{ latestVital.diastolic_bp }}<span>mmHg</span></div>
                </div>
              </li>
              <li v-if="latestVital.blood_glucose" class="dash-vital-row" style="--vc:#059669;--vbg:#D1FAE5;">
                <span class="dash-vital-icon">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                </span>
                <div class="dash-vital-meta">
                  <div class="dash-vital-label">Đường huyết</div>
                  <div class="dash-vital-val">{{ latestVital.blood_glucose }}<span>mmol/L</span></div>
                </div>
              </li>
            </ul>
            <div v-if="latestVital" class="dash-vitals-recorded">
              Ghi nhận {{ new Date(latestVital.recorded_at).toLocaleDateString('vi-VN') }}
            </div>
          </template>
        </section>

        <!-- Interactions safety card -->
        <section class="dash-card dash-inter-card" @click="router.push('/interactions')" style="cursor:pointer;">
          <div class="dash-inter-flag">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
            Kiểm tra tương tác
          </div>
          <h3 class="dash-inter-title">Tra cứu tương tác thuốc</h3>
          <p class="dash-inter-sub">Kiểm tra an toàn cho các thuốc đang dùng của bạn.</p>
          <span class="dash-link" style="margin-top:auto;">Kiểm tra ngay →</span>
        </section>

        <!-- AI recommendations card -->
        <section class="dash-card dash-rec-card" @click="router.push('/recommendations')" style="cursor:pointer;">
          <div class="dash-rec-inner">
            <div>
              <div class="dash-eyebrow" style="color:rgba(255,255,255,.65);">GỢI Ý THÔNG MINH</div>
              <h3 class="dash-rec-title">Nhận gợi ý thuốc từ AI</h3>
              <p class="dash-rec-sub">Nhập triệu chứng và nhận gợi ý phù hợp hồ sơ sức khoẻ.</p>
            </div>
            <button class="dash-rec-btn">Thử ngay →</button>
          </div>
          <div class="dash-rec-glow" aria-hidden="true"></div>
        </section>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Root ───────────────────────────────────────────────────────────────────── */
.dash-root {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── Row 1: Hero + Stats ────────────────────────────────────────────────────── */
.dash-row1 {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 20px;
}
@media (max-width: 960px) { .dash-row1 { grid-template-columns: 1fr; } }

/* Hero */
.dash-hero {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  background: linear-gradient(130deg, #142853 0%, #1E3568 45%, #2563EB 100%);
  min-height: 200px;
}
.dash-hero-bg { position: absolute; inset: 0; pointer-events: none; }
.dash-hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 32px;
}
.dash-hero-left { flex: 1; display: flex; flex-direction: column; gap: 16px; }
.dash-hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  color: rgba(255,255,255,.65);
}
.dash-pulse {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #4ADE80;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.6;transform:scale(1.3)} }

.dash-hero-counter { display: flex; align-items: center; gap: 20px; }
.dash-hero-time { display: flex; flex-direction: column; gap: 2px; }
.dash-hero-time-num { font-size: 40px; font-weight: 800; color: #fff; line-height: 1; letter-spacing: -1px; }
.dash-hero-time-meta { font-size: 13px; color: rgba(255,255,255,.6); }
.dash-hero-time-meta b { color: rgba(255,255,255,.9); }
.dash-hero-divider { width: 1px; height: 56px; background: rgba(255,255,255,.18); flex-shrink: 0; }
.dash-hero-drug-name { font-size: 22px; font-weight: 700; color: #fff; letter-spacing: -.3px; }
.dash-hero-drug-meta { font-size: 13px; color: rgba(255,255,255,.6); margin-top: 2px; }

.dash-hero-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.dash-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; border-radius: 12px;
  background: #fff; color: #142853;
  font-size: 13px; font-weight: 700;
  border: none; cursor: pointer;
  transition: opacity .15s;
}
.dash-btn-primary:hover { opacity: .92; }
.dash-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.dash-btn-ghost {
  padding: 9px 16px; border-radius: 12px;
  background: rgba(255,255,255,.12); color: rgba(255,255,255,.82);
  font-size: 13px; font-weight: 600;
  border: none; cursor: pointer;
  transition: background .15s;
}
.dash-btn-ghost:hover { background: rgba(255,255,255,.2); }

.dash-hero-aside {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding-left: 24px;
  border-left: 1px solid rgba(255,255,255,.12);
  min-width: 140px;
}
.dash-hero-pill-icon {
  width: 56px; height: 56px; border-radius: 16px;
  background: rgba(255,255,255,.12);
  display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,.85);
}
.dash-hero-aside-meta { text-align: center; }
.dash-hero-aside-label { font-size: 11px; font-weight: 700; letter-spacing: .08em; color: rgba(255,255,255,.5); text-transform: uppercase; }
.dash-hero-aside-val { font-size: 16px; font-weight: 800; color: #fff; margin-top: 2px; }
.dash-hero-aside-sub { font-size: 11px; color: rgba(255,255,255,.5); margin-top: 4px; }

/* Stats card */
.dash-stats-card {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  border: 1px solid rgba(12,29,66,.08);
  box-shadow: 0 1px 2px rgba(12,29,66,.04);
  display: flex; flex-direction: column; gap: 16px;
}
.dash-stats-head { display: flex; align-items: center; justify-content: space-between; }
.dash-stats-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #8A95AC; }
.dash-stats-admin { display: flex; flex-direction: column; gap: 2px; font-size: 11px; color: #5A6985; text-align: right; }
.dash-stats-ring-wrap {
  position: relative; width: 110px; height: 110px;
  margin: 0 auto;
}
.dash-ring-svg { width: 100%; height: 100%; }
.dash-ring-center {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.dash-ring-num { font-size: 24px; font-weight: 800; color: #0C1D42; line-height: 1; }
.dash-ring-num span { font-size: 16px; font-weight: 600; color: #8A95AC; }
.dash-ring-lbl { font-size: 11px; color: #8A95AC; margin-top: 2px; }
.dash-stats-bars { display: flex; flex-direction: column; gap: 10px; }
.dash-stat-bar { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.dash-stat-bar span { flex: 1; color: #5A6985; }
.dash-bar-track {
  width: 56px; height: 5px; border-radius: 3px;
  background: rgba(12,29,66,.07); overflow: hidden; flex-shrink: 0;
}
.dash-bar-track i { display: block; height: 100%; border-radius: 3px; background: #2563EB; transition: width .4s; }
.dash-stat-bar b { width: 28px; text-align: right; font-weight: 700; color: #0C1D42; }

/* ── Row 2: Quick actions ────────────────────────────────────────────────────── */
.dash-qa {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
@media (max-width: 800px) { .dash-qa { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px) { .dash-qa { grid-template-columns: 1fr; } }

.dash-qa-tile {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 16px;
  background: #fff; text-align: left;
  border: 1px solid rgba(12,29,66,.08);
  box-shadow: 0 1px 2px rgba(12,29,66,.04);
  cursor: pointer; transition: box-shadow .15s, transform .15s;
}
.dash-qa-tile:hover {
  box-shadow: 0 4px 20px -4px rgba(12,29,66,.12);
  transform: translateY(-1px);
}
.dash-qa-icon {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.dash-qa-text { flex: 1; min-width: 0; }
.dash-qa-text b { display: block; font-size: 13px; font-weight: 700; color: #0C1D42; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dash-qa-text em { display: block; font-size: 11px; font-style: normal; color: #8A95AC; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dash-qa-arrow { width: 16px; height: 16px; color: #C8D0DC; flex-shrink: 0; }

/* ── Row 3: Schedule + Side ──────────────────────────────────────────────────── */
.dash-row3 {
  display: grid;
  grid-template-columns: 1fr 296px;
  gap: 20px;
  align-items: start;
}
@media (max-width: 1100px) { .dash-row3 { grid-template-columns: 1fr; } }

/* ── Card base ───────────────────────────────────────────────────────────────── */
.dash-card {
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(12,29,66,.08);
  box-shadow: 0 1px 2px rgba(12,29,66,.04);
  overflow: hidden;
}
.dash-card-h {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(12,29,66,.06);
}
.dash-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #8A95AC; margin-bottom: 2px; }
.dash-card-title { font-size: 16px; font-weight: 700; color: #0C1D42; letter-spacing: -.2px; }
.dash-card-title-sm { font-size: 14px; font-weight: 700; color: #0C1D42; letter-spacing: -.1px; }
.dash-card-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; flex-wrap: wrap; }
.dash-tab-btn {
  padding: 5px 12px; border-radius: 8px; font-size: 12px; font-weight: 600;
  border: 1px solid rgba(12,29,66,.10); background: #F3F5F7; color: #5A6985;
  cursor: pointer; transition: all .15s;
}
.dash-tab-btn.is-on { background: #0C1D42; color: #fff; border-color: #0C1D42; }
.dash-date-nav {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(12,29,66,.10); background: #F3F5F7; color: #5A6985;
  cursor: pointer; transition: all .15s;
}
.dash-date-nav:hover:not(:disabled) { background: #EFF3F8; }
.dash-date-nav:disabled { opacity: .35; cursor: not-allowed; }
.dash-date-input {
  padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: 500;
  border: 1px solid rgba(12,29,66,.10); background: #F3F5F7; color: #0C1D42;
  font-family: inherit; cursor: pointer;
}

/* Timeline ruler */
.dash-timeline {
  position: relative;
  height: 36px;
  margin: 0 20px;
  border-bottom: 1px solid rgba(12,29,66,.06);
}
.dash-tick {
  position: absolute; top: 0; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center;
}
.dash-tick::before {
  content: '';
  display: block; width: 1px; height: 8px;
  background: rgba(12,29,66,.15);
}
.dash-tick span { font-size: 10px; color: #8A95AC; margin-top: 2px; white-space: nowrap; }
.dash-now-marker {
  position: absolute; top: 0; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center;
  z-index: 2;
}
.dash-now-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #EF4444;
  box-shadow: 0 0 0 2px rgba(239,68,68,.25);
}
.dash-now-lbl { font-size: 10px; font-weight: 700; color: #EF4444; margin-top: 2px; white-space: nowrap; }
.dash-blip {
  position: absolute; top: 0; width: 4px; height: 4px;
  border-radius: 50%; transform: translate(-50%, 16px);
}

/* Dose list */
.dash-dose-list { list-style: none; margin: 0; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
.dash-dose {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 14px;
  transition: background .12s;
  border: 1px solid transparent;
}
.dash-dose:hover { background: #F8FAFB; }
.dash-dose.is-done { opacity: .72; }
.dash-dose.is-next { background: #F0F7FF; border-color: rgba(37,99,235,.15); }

.dash-check-btn {
  width: 22px; height: 22px; border-radius: 50%;
  border: 2px solid rgba(12,29,66,.15);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; cursor: pointer; background: transparent;
  transition: all .15s;
}
.dash-check-btn:hover:not(:disabled) { border-color: #2563EB; }
.dash-check-btn:disabled { cursor: default; }

.dash-dose-time { width: 44px; flex-shrink: 0; }
.dash-dose-time-num { font-size: 13px; font-weight: 700; color: #0C1D42; }

.dash-dose-pill-icon {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.dash-dose-body { flex: 1; min-width: 0; }
.dash-dose-drug { font-size: 14px; font-weight: 700; color: #0C1D42; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dash-dose-meta { font-size: 12px; color: #8A95AC; margin-top: 1px; }
.dash-dose-tag { color: #5A6985; }

.dash-status-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 700; white-space: nowrap; flex-shrink: 0;
}
.dash-pulse-sm {
  width: 5px; height: 5px; border-radius: 50%; background: #2563EB;
  animation: pulse 1.4s infinite;
}

/* Loading / empty */
.dash-loading { padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.dash-skeleton {
  height: 60px; border-radius: 14px;
  background: linear-gradient(90deg, #F3F5F7 25%, #EFF3F8 50%, #F3F5F7 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.dash-empty {
  text-align: center; padding: 40px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}

/* ── Side panels ─────────────────────────────────────────────────────────────── */
.dash-side-panels { display: flex; flex-direction: column; gap: 16px; }

/* Vitals */
.dash-vitals-card {}
.dash-vitals-list { list-style: none; margin: 0; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
.dash-vital-row {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 12px;
  background: rgba(0,0,0,.018);
}
.dash-vital-icon {
  width: 28px; height: 28px; border-radius: 8px;
  background: var(--vbg); color: var(--vc);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.dash-vital-meta { flex: 1; }
.dash-vital-label { font-size: 11px; color: #8A95AC; }
.dash-vital-val { font-size: 15px; font-weight: 700; color: #0C1D42; line-height: 1.2; }
.dash-vital-val span { font-size: 11px; font-weight: 500; color: #8A95AC; margin-left: 2px; }
.dash-vitals-recorded { padding: 8px 14px 12px; font-size: 11px; color: #B5BCCB; text-align: right; }
.dash-empty-sm {
  padding: 20px; text-align: center; font-size: 13px; color: #8A95AC;
  display: flex; flex-direction: column; gap: 6px; align-items: center;
}
.dash-link {
  background: none; border: none; padding: 0;
  font-size: 13px; font-weight: 600; color: #2563EB; cursor: pointer;
  text-decoration: none;
}
.dash-link:hover { text-decoration: underline; }

/* Vitals form */
.dash-vitals-form {
  padding: 12px; display: flex; flex-direction: column; gap: 10px;
}
.dash-vitals-form-row { display: flex; flex-direction: column; gap: 3px; }
.dash-vitals-form-row label { font-size: 11px; font-weight: 600; color: #5A6985; }
.dash-vitals-form-row input {
  padding: 7px 10px; border-radius: 9px;
  border: 1px solid rgba(12,29,66,.14); background: #F8FAFB;
  font-size: 13px; color: #0C1D42; font-family: inherit;
  outline: none; transition: border-color .15s;
}
.dash-vitals-form-row input:focus { border-color: #2563EB; background: #fff; }
.dash-btn-primary-sm {
  padding: 9px 16px; border-radius: 10px;
  background: #2563EB; color: #fff;
  font-size: 13px; font-weight: 700;
  border: none; cursor: pointer;
  transition: opacity .15s;
}
.dash-btn-primary-sm:hover { opacity: .9; }
.dash-btn-primary-sm:disabled { opacity: .5; cursor: not-allowed; }

/* Interactions card */
.dash-inter-card {
  padding: 18px; display: flex; flex-direction: column; gap: 8px;
  min-height: 130px;
}
.dash-inter-flag {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  background: #D1FAE5; color: #065F46;
  font-size: 11px; font-weight: 700; align-self: flex-start;
}
.dash-inter-title { font-size: 15px; font-weight: 700; color: #0C1D42; }
.dash-inter-sub { font-size: 12px; color: #5A6985; line-height: 1.5; }

/* Recommendations card */
.dash-rec-card {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #2563EB, #1D4FD8) !important;
  border: none !important;
  padding: 0;
}
.dash-rec-inner {
  position: relative; z-index: 1;
  padding: 20px; display: flex; flex-direction: column; gap: 10px;
}
.dash-rec-title { font-size: 16px; font-weight: 700; color: #fff; letter-spacing: -.2px; }
.dash-rec-sub { font-size: 12px; color: rgba(255,255,255,.65); line-height: 1.5; }
.dash-rec-btn {
  padding: 9px 16px; border-radius: 10px;
  background: rgba(255,255,255,.15); color: #fff;
  font-size: 13px; font-weight: 700;
  border: none; cursor: pointer;
  transition: background .15s; align-self: flex-start;
}
.dash-rec-btn:hover { background: rgba(255,255,255,.25); }
.dash-rec-glow {
  position: absolute; right: -20px; bottom: -20px;
  width: 100px; height: 100px; border-radius: 50%;
  background: rgba(255,255,255,.07); pointer-events: none;
}
</style>
