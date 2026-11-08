import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/templates' },
    {
      path: '/generation',
      name: 'generation',
      component: () => import('../views/generation/GenerationStart.vue'),
      meta: { title: '智能制证' },
    },
    {
      path: '/generation/:taskId',
      name: 'generation-result',
      component: () => import('../views/generation/GenerationResult.vue'),
      meta: { title: '制证结果' },
    },
    {
      path: '/accounts',
      name: 'accounts',
      component: () => import('../views/accounts/AccountList.vue'),
      meta: { title: '会计科目' },
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('../views/templates/TemplateList.vue'),
      meta: { title: '凭证模板' },
    },
    {
      path: '/templates/new',
      name: 'template-create',
      component: () => import('../views/templates/TemplateEditor.vue'),
      meta: { title: '新建凭证模板' },
    },
    {
      path: '/templates/:id/edit',
      name: 'template-edit',
      component: () => import('../views/templates/TemplateEditor.vue'),
      meta: { title: '编辑凭证模板' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFound.vue'),
      meta: { title: '页面不存在' },
    },
  ],
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 智能制证` : '智能制证'
})

export default router
