import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { resourcesApi } from '@/api'
import type { ResourceTreeNode } from '@/api/resources'

export interface MenuItem {
  key: string
  label: string
  icon: string
  route: string
  expandable?: boolean
  children?: MenuItem[]
  requires_admin?: boolean
}

export const useMenuStore = defineStore('menu', () => {
  // State
  const menuResources = ref<ResourceTreeNode[]>([])
  const isLoading = ref(false)
  const lastFetchTime = ref<number>(0)
  
  // Cache duration: 5 minutes
  const CACHE_DURATION = 5 * 60 * 1000
  
  // Getters
  const upperNavItems = computed(() => {
    const items: MenuItem[] = []
    
    menuResources.value.forEach(resource => {
      if (resource.type === 'menu' && !resource.path?.startsWith('/system') && !isManagementMenu(resource.path || '')) {
        items.push({
          key: getRouteKey(resource.path || ''),
          label: resource.name,
          icon: resource.icon || 'Menu',
          route: resource.path || '/'
        })
      }
    })
    
    return items
  })
  
  const lowerNavItems = computed(() => {
    const items: MenuItem[] = []
    
    menuResources.value.forEach(resource => {
      if (resource.type === 'menu') {
        if (resource.path === '/system' && resource.children) {
          // 系统管理菜单
          const systemChildren: MenuItem[] = []
          resource.children.forEach(child => {
            systemChildren.push({
              key: getRouteKey(child.path || ''),
              label: child.name,
              icon: child.icon || 'Setting',
              route: child.path || '/'
            })
          })
          
          items.push({
            key: 'system',
            label: '系统管理',
            icon: 'Setting',
            route: '/system',
            expandable: true,
            children: systemChildren,
            requires_admin: true
          })
        } else if (isManagementMenu(resource.path || '')) {
          // 其他管理功能菜单
          items.push({
            key: getRouteKey(resource.path || ''),
            label: resource.name,
            icon: resource.icon || 'Setting',
            route: resource.path || '/'
          })
        }
      }
    })
    
    return items
  })
  
  // Helper functions
  const getRouteKey = (path: string): string => {
    const segments = path.split('/').filter(Boolean)
    return segments[segments.length - 1] || 'home'
  }
  
  const isManagementMenu = (path: string): boolean => {
    const managementPaths = ['/knowledge-base', '/workflow-editor', '/agent-management', '/profile']
    return managementPaths.includes(path)
  }
  
  const shouldRefreshCache = (): boolean => {
    return Date.now() - lastFetchTime.value > CACHE_DURATION
  }
  
  // Actions
  const fetchUserMenuResources = async (forceRefresh = false) => {
    if (!forceRefresh && menuResources.value.length > 0 && !shouldRefreshCache()) {
      return menuResources.value
    }
    
    try {
      isLoading.value = true
      const response = await resourcesApi.getUserMenuResources()
      menuResources.value = response.data
      lastFetchTime.value = Date.now()
      
      return menuResources.value
    } catch (error: any) {
      console.error('Failed to fetch user menu resources:', error)
      ElMessage.error('获取菜单失败')
      
      // 如果获取失败，返回默认菜单
      if (menuResources.value.length === 0) {
        menuResources.value = getDefaultMenuResources()
      }
      
      return menuResources.value
    } finally {
      isLoading.value = false
    }
  }
  
  const getDefaultMenuResources = (): ResourceTreeNode[] => {
    return [
      {
        id: 1,
        name: '智能问答',
        code: 'CHAT',
        type: 'menu',
        path: '/chat',
        icon: 'ChatDotRound',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 2,
        name: '智能问数',
        code: 'SMART_QUERY',
        type: 'menu',
        path: '/smart-query',
        icon: 'DataAnalysis',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 3,
        name: '智能创作',
        code: 'CREATION',
        type: 'menu',
        path: '/creation',
        icon: 'EditPen',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 4,
        name: '智能体市场',
        code: 'MARKET',
        type: 'menu',
        path: '/market',
        icon: 'Shop',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 5,
        name: '知识库',
        code: 'KNOWLEDGE',
        type: 'menu',
        path: '/knowledge',
        icon: 'Collection',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 6,
        name: '工作流编排',
        code: 'WORKFLOW',
        type: 'menu',
        path: '/workflow',
        icon: 'Connection',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 7,
        name: '智能体管理',
        code: 'AGENT',
        type: 'menu',
        path: '/agent',
        icon: 'Robot',
        requires_auth: true,
        requires_admin: false
      },
      {
        id: 8,
        name: '个人资料',
        code: 'PROFILE',
        type: 'menu',
        path: '/profile',
        icon: 'User',
        requires_auth: true,
        requires_admin: false
      }
    ]
  }
  
  const clearCache = () => {
    menuResources.value = []
    lastFetchTime.value = 0
  }
  
  const clearMenuResources = () => {
    menuResources.value = []
  }

  return {
    // State
    menuResources,
    isLoading,
    
    // Getters
    upperNavItems,
    lowerNavItems,
    
    // Actions
    fetchUserMenuResources,
    clearCache,
    clearMenuResources
  }
})