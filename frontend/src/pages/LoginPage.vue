<template>
  <div class="login">
    <section class="login__plate">
      <div class="login__plate-top">
        <span class="eyebrow">安衡合规咨询 · 法规监测组</span>
        <span class="label">卷宗 00 / 校勘</span>
      </div>

      <div class="login__glyph-row">
        <div class="login__glyph serif">第</div>
        <div class="login__glyph-meta">
          <div class="login__vertical serif">法規標準更新採集與條款變更比對</div>
          <div class="login__seal">合規監測</div>
        </div>
      </div>

      <div class="login__brand">
        <div class="display login__brand-name">lawdelta</div>
        <p class="login__brand-sub">
          每周从三个来源采集法规新版本，按「第X条」切分对齐，把编号重排的噪声压掉，
          只留下真正改动的条款，并给出重大 / 一般 / 编辑性三级判断。
        </p>
      </div>

      <div class="login__specimen">
        <div class="specimen__col">
          <div class="label">采集来源</div>
          <ul class="specimen__list">
            <li>国家标准全文公开系统</li>
            <li>市场监管总局规章库</li>
            <li>地方生态环境厅文件</li>
          </ul>
        </div>
        <div class="specimen__col">
          <div class="label">落库口径</div>
          <ul class="specimen__list">
            <li>3 来源 · 2 部法规 · 6 个版本</li>
            <li>2 次比对 · 9 条变更</li>
            <li>编号重排版：0 误报</li>
          </ul>
        </div>
      </div>

      <div class="login__plate-foot">
        <span>台账起始 2026-11</span>
        <span>algorithm v1.0.0</span>
      </div>
    </section>

    <section class="login__form-wrap">
      <div class="login__form rise">
        <div class="eyebrow">sign in</div>
        <h2 class="display login__title">进入校勘台</h2>
        <p class="login__desc">用监测组账号登录：合规总监可发布变更，分析师可采集与确认，客户只读。</p>

        <form class="login__form-body" @submit.prevent="submit">
          <label class="login__field">
            <span class="label">邮箱</span>
            <input
              v-model="email"
              type="email"
              class="field"
              autocomplete="username"
              data-test="login-email"
              placeholder="admin@lawdelta.io"
            />
          </label>
          <label class="login__field">
            <span class="label">密码</span>
            <input
              v-model="password"
              type="password"
              class="field"
              autocomplete="current-password"
              data-test="login-password"
              placeholder="Demo@2026"
            />
          </label>
          <button
            type="submit"
            class="btn btn--solid login__submit"
            data-test="login-submit"
            :disabled="auth.loading"
          >
            {{ auth.loading ? '校验中…' : '登录' }}
          </button>
        </form>

        <ErrorNotice :error="error" :retryable="false" />

        <div class="login__accounts">
          <div class="label">演示账号 · 密码统一 Demo@2026</div>
          <ul>
            <li v-for="account in demoAccounts" :key="account.email">
              <button class="login__account" type="button" @click="fill(account.email)">
                <span class="login__account-role">{{ account.role }}</span>
                <span class="login__account-mail">{{ account.email }}</span>
                <span class="login__account-hint">{{ account.hint }}</span>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import { useAuthStore } from '../stores/authStore'
import type { ApiError } from '../types/api'

const router = useRouter()
const auth = useAuthStore()

const email = ref('admin@lawdelta.io')
const password = ref('Demo@2026')
const error = ref<ApiError | null>(null)

const demoAccounts = [
  { role: '合规总监', email: 'admin@lawdelta.io', hint: '来源 · 比对 · 发布' },
  { role: '法规分析师', email: 'analyst@lawdelta.io', hint: '采集 · 比对 · 确认' },
  { role: '客户只读', email: 'viewer@lawdelta.io', hint: '仅已发布说明' },
]

function fill(value: string) {
  email.value = value
  password.value = 'Demo@2026'
  error.value = null
}

async function submit() {
  error.value = null
  try {
    await auth.login(email.value.trim(), password.value)
    await router.push('/documents')
  } catch (caught) {
    error.value = caught as ApiError
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(0, 1fr);
}

.login__plate {
  border-right: 1px solid var(--rule);
  background: var(--paper-2);
  padding: clamp(24px, 4vw, 52px) clamp(26px, 5vw, 66px);
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  overflow: hidden;
}
.login__plate::after {
  content: '';
  position: absolute;
  inset: 18px;
  border: 1px solid var(--rule-soft);
  pointer-events: none;
}
.login__plate-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  position: relative;
  z-index: 1;
}
.login__glyph-row {
  display: flex;
  gap: 22px;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}
.login__glyph {
  font-size: clamp(88px, 12vw, 150px);
  line-height: 0.82;
  color: var(--ink);
  letter-spacing: -0.04em;
}
.login__glyph-meta {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding-top: 8px;
}
.login__vertical {
  writing-mode: vertical-rl;
  font-size: 12px;
  letter-spacing: 0.3em;
  color: var(--ink-soft);
  border-left: 1px solid var(--rule);
  padding-left: 9px;
}
.login__seal {
  writing-mode: vertical-rl;
  font-family: var(--serif);
  font-size: 15px;
  letter-spacing: 0.28em;
  color: var(--seal);
  border: 2px solid var(--seal);
  padding: 7px 5px;
  transform: rotate(-2.4deg);
}
.login__brand {
  margin-top: auto;
  position: relative;
  z-index: 1;
}
.login__brand-name {
  font-size: clamp(30px, 3.4vw, 44px);
  letter-spacing: -0.02em;
}
.login__brand-sub {
  margin-top: 9px;
  max-width: 46ch;
  font-size: 12px;
  line-height: 1.85;
  color: var(--ink-soft);
}
.login__specimen {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 22px;
  border-top: 1px solid var(--rule);
  padding-top: 16px;
  position: relative;
  z-index: 1;
}
.specimen__list {
  margin: 7px 0 0;
  padding: 0;
  list-style: none;
  font-family: var(--serif);
  font-size: 12px;
  line-height: 1.95;
  color: var(--ink-soft);
}
.login__plate-foot {
  display: flex;
  justify-content: space-between;
  font-size: 9.5px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
  position: relative;
  z-index: 1;
}

.login__form-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 28px;
}
.login__form {
  width: min(360px, 100%);
}
.login__title {
  font-size: 25px;
  margin-top: 7px;
}
.login__desc {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.75;
  color: var(--ink-soft);
}
.login__form-body {
  margin-top: 26px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.login__field {
  display: block;
}
.login__field .label {
  display: block;
  margin-bottom: 5px;
}
.login__submit {
  justify-content: center;
  padding: 10px;
  margin-top: 4px;
}
.login__accounts {
  margin-top: 28px;
  border-top: 1px solid var(--rule-soft);
  padding-top: 14px;
}
.login__accounts ul {
  list-style: none;
  margin: 9px 0 0;
  padding: 0;
}
.login__account {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr);
  gap: 2px 10px;
  width: 100%;
  text-align: left;
  background: none;
  border: 0;
  border-bottom: 1px dotted var(--rule-soft);
  padding: 6px 0;
  cursor: pointer;
  color: var(--ink-soft);
}
.login__account:hover {
  color: var(--ink);
}
.login__account-role {
  font-family: var(--serif);
  font-size: 12px;
  color: var(--seal);
}
.login__account-mail {
  font-size: 11.5px;
}
.login__account-hint {
  grid-column: 2;
  font-size: 10px;
  color: var(--ink-faint);
}

@media (max-width: 900px) {
  .login {
    grid-template-columns: minmax(0, 1fr);
  }
  .login__plate {
    border-right: 0;
    border-bottom: 1px solid var(--rule);
    gap: 18px;
  }
  .login__specimen {
    display: none;
  }
}
</style>
