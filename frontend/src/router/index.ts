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
        redirect: '/workflow/list',
        meta: { requiresAuth: true },
        children: [
          {
            path: 'list',
            name: 'WorkflowList',
            component: () => import('../views/WorkflowList.vue'),
            meta: { requiresAuth: true }
          },
          {
            path: 'editor/:id?',
            name: 'WorkflowEditor',
            component: () => import('../components/WorkflowEditor.vue'),
            meta: { requiresAuth: true }
          }
        ]
      },
      {
        path: 'agent',
        name: 'Agent',
        component: () => import('../components/AgentManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'smart-query',
        name: 'SmartQuery',
        component: () => import('../components/SmartQuery.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'creation',
        name: 'Creation',
        component: () => import('../components/CreativeStudio.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('../views/SystemManagement.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
        redirect: '/system/users',
        children: [
          {
            path: 'users',
            name: 'SystemUsers',
            component: () => import('../components/system/UserManagement.vue'),
            meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' }
          },
          {
            path: 'departments',
            name: 'SystemDepartments',
            component: () => import('../components/system/DepartmentManagement.vue'),
            meta: { requiresAuth: true, requiresAdmin: true, title: '部门管理' }
          },
          {
            path: 'roles',
            name: 'SystemRoles',
            component: () => import('../components/system/RoleManagement.vue'),
            meta: { requiresAuth: true, requiresAdmin: true, title: '角色管理' }
          },

          {
            path: 'llm-configs',
            name: 'SystemLLMConfigs',
            component: () => import('../components/system/LLMConfigManagement.vue'),
            meta: { requiresAuth: true, requiresAdmin: true, title: '大模型管理' }
          }
        ]
      }
    ]
  },
  {
    path: '/paste',
    name: 'Paste',
    component: () => import('../views/Paste.vue'),
    meta: { requiresAuth: false }
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
    document.title = `${to.meta.title} - openAgent`
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
  
  // Check admin requirement
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    next({ name: 'Chat' })
    return
  }
  
  // Redirect authenticated users away from login/register
  // 但如果是因为token过期跳转过来的，则允许访问登录页面
  if ((to.name === 'Login' || to.name === 'Register') && userStore.isAuthenticated && !to.query.expired) {
    next({ name: 'Chat' })
    return
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router