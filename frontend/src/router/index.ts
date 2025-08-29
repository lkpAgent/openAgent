import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import NProgress from 'nprogress'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'MainLayout',
    component: () => import('../components/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../components/KnowledgeManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'workflow',
        name: 'Workflow',
        component: () => import('../components/WorkflowEditor.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'agent',
        name: 'Agent',
        component: () => import('../components/AgentManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  // Set page title
  if (to.meta.title) {
    document.title = `${to.meta.title} - ChatAgent`
  }
  
  const userStore = useUserStore()
  
  // Initialize user if token exists
  if (!userStore.user && localStorage.getItem('access_token')) {
    try {
      await userStore.initializeUser()
    } catch (error) {
      console.log('Failed to initialize user')
    }
  }
  
  // Check authentication requirement
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  // Redirect authenticated users away from login/register
  if ((to.name === 'Login' || to.name === 'Register') && userStore.isAuthenticated) {
    next({ name: 'Chat' })
    return
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router