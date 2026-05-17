<script setup lang="ts">
import { computed, ref } from 'vue'
import { useInteractionExplain } from '@/api/interaction-explain.api'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'

const props = defineProps<{
  drugId1: string
  drugId2: string
}>()

const open = ref(false)
const requested = ref(false)
const openSections = ref<Record<string, boolean>>({})

const drugId1Ref = computed(() => props.drugId1)
const drugId2Ref = computed(() => props.drugId2)
const { data, isError, isPending } = useInteractionExplain(drugId1Ref, drugId2Ref, requested)

const severityClass = computed(() => {
  if (data.value?.severity_color === 'red') return 'explain-severity-red'
  if (data.value?.severity_color === 'yellow') return 'explain-severity-yellow'
  return 'explain-severity-amber'
})

const usageBanner = computed(() => {
  if (data.value?.can_be_used_together === true) {
    return {
      className: 'explain-banner-green',
      text: 'Có thể dùng đồng thời khi có chỉ dẫn của bác sĩ',
    }
  }
  if (data.value?.can_be_used_together === false) {
    return {
      className: 'explain-banner-red',
      text: 'Không nên dùng đồng thời — hỏi bác sĩ về thuốc thay thế',
    }
  }
  return {
    className: 'explain-banner-amber',
    text: 'Tuỳ tình huống — tham khảo bác sĩ hoặc dược sĩ',
  }
})

function openSheet() {
  open.value = true
  requested.value = true
}

function closeSheet() {
  open.value = false
}

function toggleSection(key: string) {
  openSections.value = {
    ...openSections.value,
    [key]: !openSections.value[key],
  }
}
</script>

<template>
  <AppButton variant="ghost" size="sm" class="explain-trigger" @click.stop="openSheet">
    Giải thích chi tiết ✨
  </AppButton>

  <Teleport to="body">
    <Transition name="explain-sheet">
      <div v-if="open" class="explain-root" @click.self="closeSheet">
        <section class="explain-panel" role="dialog" aria-modal="true" aria-label="Giải thích tương tác thuốc">
          <header class="explain-topbar">
            <div>
              <p class="explain-eyebrow">Giải thích tương tác</p>
              <h2 class="explain-title">Thông tin dược học chi tiết</h2>
            </div>
            <button class="explain-close" type="button" aria-label="Đóng" @click="closeSheet">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </header>

          <div v-if="isPending" class="explain-loading">
            <AppSkeleton :lines="4" />
          </div>

          <div v-else-if="isError" class="explain-error">
            Không thể tải giải thích. Thử lại sau.
          </div>

          <div v-else-if="data" class="explain-content">
            <div class="explain-pair">
              <span>{{ data.drug_a_name }}</span>
              <span class="explain-warning">⚠️</span>
              <span>{{ data.drug_b_name }}</span>
            </div>

            <div class="explain-meta-row">
              <span :class="['explain-severity', severityClass]">{{ data.severity }}</span>
              <span v-if="data.from_cache" class="explain-cache">⚡ Từ bộ nhớ đệm</span>
            </div>

            <p class="explain-summary">{{ data.summary }}</p>

            <div :class="['explain-usage', usageBanner.className]">
              {{ usageBanner.text }}
            </div>

            <div class="explain-accordion">
              <article class="explain-section">
                <button type="button" class="explain-section-button" @click="toggleSection('mechanism')">
                  <span>🔬 Cơ chế tương tác</span>
                  <span :class="['explain-section-icon', openSections.mechanism ? 'is-open' : '']">⌄</span>
                </button>
                <p v-if="openSections.mechanism" class="explain-section-body">{{ data.mechanism }}</p>
              </article>

              <article class="explain-section">
                <button type="button" class="explain-section-button" @click="toggleSection('symptoms')">
                  <span>👁️ Triệu chứng cần theo dõi</span>
                  <span :class="['explain-section-icon', openSections.symptoms ? 'is-open' : '']">⌄</span>
                </button>
                <ul v-if="openSections.symptoms" class="explain-list">
                  <li v-for="item in data.symptoms_to_watch" :key="item">{{ item }}</li>
                  <li v-if="data.symptoms_to_watch.length === 0">Chưa có triệu chứng cụ thể được ghi nhận.</li>
                </ul>
              </article>

              <article class="explain-section">
                <button type="button" class="explain-section-button" @click="toggleSection('actions')">
                  <span>✅ Khuyến nghị</span>
                  <span :class="['explain-section-icon', openSections.actions ? 'is-open' : '']">⌄</span>
                </button>
                <ol v-if="openSections.actions" class="explain-list explain-list-numbered">
                  <li v-for="item in data.what_to_do" :key="item">{{ item }}</li>
                </ol>
              </article>

              <article class="explain-section">
                <button type="button" class="explain-section-button" @click="toggleSection('doctor')">
                  <span>🚨 Khi nào gặp bác sĩ</span>
                  <span :class="['explain-section-icon', openSections.doctor ? 'is-open' : '']">⌄</span>
                </button>
                <p v-if="openSections.doctor" class="explain-section-body">{{ data.when_to_see_doctor }}</p>
              </article>
            </div>

            <footer class="explain-footer">
              <span :class="['explain-source', data.source === 'model_predicted' ? 'is-ai' : 'is-db']">
                {{ data.source === 'model_predicted' ? 'Nguồn: AI dự đoán' : 'Nguồn: Cơ sở dữ liệu' }}
              </span>
              <p v-if="data.confidence_note" class="explain-confidence">{{ data.confidence_note }}</p>
              <p class="explain-disclaimer">{{ data.disclaimer }}</p>
            </footer>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.explain-trigger {
  border-radius: 999px;
  font-size: 11.5px;
  padding: 6px 10px;
}

.explain-root {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(15, 23, 20, 0.42);
  padding: 16px;
}

.explain-panel {
  width: min(680px, 100%);
  max-height: min(86vh, 760px);
  overflow: auto;
  border-radius: 22px 22px 16px 16px;
  background: #ffffff;
  box-shadow: 0 24px 70px -28px rgba(15, 23, 42, 0.52);
  border: 1px solid #e6e6e0;
}

.explain-topbar {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px 14px;
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid #e6e6e0;
  backdrop-filter: blur(12px);
}

.explain-eyebrow {
  margin: 0 0 3px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #68756f;
}

.explain-title {
  margin: 0;
  color: #0f1714;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 800;
}

.explain-close {
  width: 36px;
  height: 36px;
  border: 1px solid #e6e6e0;
  border-radius: 11px;
  color: #5d6b65;
  background: #fbfbf9;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.explain-loading,
.explain-content {
  padding: 20px;
}

.explain-error {
  margin: 20px;
  padding: 14px 15px;
  border-radius: 14px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  font-size: 13px;
  font-weight: 600;
}

.explain-pair {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  color: #0f1714;
  font-size: 17px;
  font-weight: 800;
  line-height: 1.35;
  text-align: center;
}

.explain-warning {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  background: #fff7ed;
}

.explain-meta-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.explain-severity {
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 800;
}

.explain-severity-red {
  background: #fee2e2;
  color: #991b1b;
}

.explain-severity-amber {
  background: #fef3c7;
  color: #92400e;
}

.explain-severity-yellow {
  background: #fef9c3;
  color: #854d0e;
}

.explain-cache {
  font-size: 11px;
  color: #64748b;
}

.explain-summary {
  margin: 18px 0 14px;
  padding: 15px 16px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #334155;
  font-size: 15px;
  line-height: 1.55;
  font-style: italic;
}

.explain-usage {
  margin-bottom: 14px;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 700;
}

.explain-banner-green {
  background: #ecfdf5;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.explain-banner-red {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.explain-banner-amber {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

.explain-accordion {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.explain-section {
  border: 1px solid #e6e6e0;
  border-radius: 14px;
  overflow: hidden;
  background: #ffffff;
}

.explain-section-button {
  width: 100%;
  border: 0;
  background: #ffffff;
  padding: 13px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #17211d;
  font-size: 13.5px;
  font-weight: 800;
  text-align: left;
  cursor: pointer;
}

.explain-section-icon {
  font-size: 18px;
  color: #64748b;
  transition: transform .16s ease;
}

.explain-section-icon.is-open {
  transform: rotate(180deg);
}

.explain-section-body,
.explain-list {
  margin: 0;
  padding: 0 14px 14px 34px;
  color: #40514a;
  font-size: 13px;
  line-height: 1.6;
}

.explain-section-body {
  padding-left: 14px;
}

.explain-list li + li {
  margin-top: 6px;
}

.explain-list-numbered {
  padding-left: 36px;
}

.explain-footer {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed #d9ded8;
}

.explain-source {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 800;
}

.explain-source.is-db {
  background: #e6f7f2;
  color: #0f766e;
}

.explain-source.is-ai {
  border: 1px dashed #f59e0b;
  color: #92400e;
  background: #fffaf0;
}

.explain-confidence {
  margin: 9px 0 0;
  color: #5d6b65;
  font-size: 12px;
  line-height: 1.5;
}

.explain-disclaimer {
  margin: 10px 0 0;
  color: #8a958f;
  font-size: 11px;
  line-height: 1.5;
}

.explain-sheet-enter-active,
.explain-sheet-leave-active {
  transition: opacity .18s ease;
}

.explain-sheet-enter-active .explain-panel,
.explain-sheet-leave-active .explain-panel {
  transition: transform .18s ease;
}

.explain-sheet-enter-from,
.explain-sheet-leave-to {
  opacity: 0;
}

.explain-sheet-enter-from .explain-panel,
.explain-sheet-leave-to .explain-panel {
  transform: translateY(18px);
}
</style>
