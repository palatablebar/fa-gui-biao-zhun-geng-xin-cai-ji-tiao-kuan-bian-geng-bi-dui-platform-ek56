<template>
  <div class="shell">
    <aside class="spine">
      <div class="spine__head">
        <div class="spine__mark">
          <span class="spine__vertical">法 典 校 勘 台</span>
          <span class="spine__seal">監</span>
        </div>
        <div>
          <div class="spine__brand">lawdelta</div>
          <div class="eyebrow mt-6">statute&nbsp;delta&nbsp;desk</div>
        </div>
      </div>

      <div class="spine__org">
        <div class="label">委托方</div>
        <div class="spine__org-name">安衡合规咨询</div>
        <div class="spine__org-sub">法规监测组 · 6 人 · 40 家客户</div>
      </div>

      <nav class="spine__nav">
        <div class="eyebrow spine__nav-title">采集与版本</div>
        <RouterLink to="/documents" class="nav-item" active-class="is-active">
          <span class="nav-item__num">壹</span>
          <span class="nav-item__label">文档版本时间线</span>
        </RouterLink>

        <div class="eyebrow spine__nav-title">比对与变更</div>
        <RouterLink to="/changes/review" class="nav-item" active-class="is-active">
          <span class="nav-item__num">貳</span>
          <span class="nav-item__label">变更确认与影响</span>
        </RouterLink>

        <div class="eyebrow spine__nav-title">客户视图</div>
        <RouterLink to="/published" class="nav-item" active-class="is-active">
          <span class="nav-item__num">參</span>
          <span class="nav-item__label">已发布变更说明</span>
        </RouterLink>
      </nav>

      <div class="spine__foot">
        <hr class="double-rule" />
        <div class="spine__user">
          <div>
            <div class="spine__user-name">{{ auth.displayName || '未登录' }}</div>
            <div class="spine__user-mail">{{ auth.email }}</div>
          </div>
          <StatusSeal :label="ROLE_LABELS[auth.role]" tone="ink" size="sm" />
        </div>
        <button class="btn btn--quiet spine__logout" data-test="logout" @click="logout">退出登录</button>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar__left">
          <span class="label">安衡合规咨询 · 法规监测组</span>
          <span class="topbar__slash">/</span>
          <span class="topbar__page">{{ route.meta.title ?? '工作台' }}</span>
        </div>
        <div class="topbar__right">
          <span class="topbar__meta">台账版本 2026-11</span>
          <span class="topbar__meta">算法 v1.0.0</span>
        </div>
      </header>
      <div class="body">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/authStore'
import { ROLE_LABELS } from '../../types/user'
import StatusSeal from './StatusSeal.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--rail) minmax(0, 1fr);
  min-height: 100vh;
}

.spine {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--rule);
  background: var(--paper-2);
  padding: 26px 20px 18px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.spine__head {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}
.spine__mark {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.spine__vertical {
  writing-mode: vertical-rl;
  font-family: var(--serif);
  font-size: 12.5px;
  letter-spacing: 0.42em;
  color: var(--ink-soft);
  border-left: 1px solid var(--rule);
  border-right: 1px solid var(--rule);
  padding: 6px 3px;
}
.spine__seal {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  font-family: var(--serif);
  font-size: 12px;
  color: var(--seal);
  border: 1px solid var(--seal);
  transform: rotate(-4deg);
}
.spine__brand {
  font-family: var(--serif);
  font-size: 25px;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1;
}
.mt-6 {
  margin-top: 6px;
}

.spine__org {
  margin-top: 22px;
  padding: 10px 0 12px;
  border-top: 1px solid var(--rule-soft);
  border-bottom: 1px solid var(--rule-soft);
}
.spine__org-name {
  font-family: var(--serif);
  font-size: 14px;
  margin-top: 4px;
}
.spine__org-sub {
  font-size: 10.5px;
  color: var(--ink-faint);
  margin-top: 2px;
}

.spine__nav {
  flex: 1;
  padding-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.spine__nav-title {
  margin: 14px 0 4px;
}
.spine__nav-title:first-child {
  margin-top: 0;
}

.nav-item {
  display: flex;
  align-items: baseline;
  gap: 9px;
  padding: 6px 8px 6px 0;
  color: var(--ink-soft);
  font-size: 12.5px;
  border-bottom: 1px solid transparent;
  transition: color 150ms var(--ease), border-color 150ms var(--ease);
}
.nav-item:hover {
  text-decoration: none;
  color: var(--ink);
}
.nav-item.is-active {
  color: var(--ink);
  border-bottom-color: var(--seal);
}
.nav-item__num {
  font-family: var(--serif);
  font-size: 12px;
  color: var(--seal);
  min-width: 14px;
}
.nav-item__label {
  font-family: var(--serif);
  letter-spacing: 0.02em;
}

.spine__foot {
  margin-top: 18px;
}
.spine__user {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
}
.spine__user-name {
  font-family: var(--serif);
  font-size: 12.5px;
}
.spine__user-mail {
  font-size: 10px;
  color: var(--ink-faint);
  word-break: break-all;
}
.spine__logout {
  margin-top: 10px;
  padding-left: 0;
  font-size: 11px;
}

.main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 10px 30px;
  border-bottom: 1px solid var(--rule-soft);
  background: color-mix(in oklch, var(--paper-2) 72%, var(--paper));
}
.topbar__left {
  display: flex;
  align-items: baseline;
  gap: 9px;
  font-size: 11px;
}
.topbar__slash {
  color: var(--rule);
}
.topbar__page {
  font-family: var(--serif);
  font-size: 12px;
  color: var(--ink);
}
.topbar__right {
  display: flex;
  gap: 16px;
}
.topbar__meta {
  font-size: 9.5px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.body {
  padding: 26px 30px 48px;
  flex: 1;
}

@media (max-width: 900px) {
  .shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .spine {
    position: static;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--rule);
    padding: 16px 18px;
  }
  .spine__head {
    align-items: center;
  }
  .spine__vertical {
    display: none;
  }
  .spine__nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 10px;
    padding-top: 10px;
  }
  .spine__nav-title {
    display: none;
  }
  .spine__org,
  .spine__foot {
    display: none;
  }
  .body {
    padding: 20px 18px 40px;
  }
}
</style>
