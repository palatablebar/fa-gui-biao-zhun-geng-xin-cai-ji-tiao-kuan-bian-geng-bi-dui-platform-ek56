import { createRouter, createWebHistory } from 'vue-router'
import { setupGuards } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/documents' },
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/LoginPage.vue'),
      meta: { public: true, title: '登录' },
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../pages/DocumentsPage.vue'),
      meta: { title: '文档版本时间线' },
    },
    {
      path: '/diffs/:id',
      name: 'diff-result',
      component: () => import('../pages/DiffResultPage.vue'),
      meta: { title: '条款比对结果' },
    },
    {
      path: '/changes/review',
      name: 'change-review',
      component: () => import('../pages/ChangeReviewPage.vue'),
      meta: { title: '变更确认与影响标注' },
    },
    {
      path: '/published',
      name: 'published',
      component: () => import('../pages/PublishedPage.vue'),
      meta: { title: '已发布变更说明' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/documents' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

setupGuards(router)

export default router
