import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUserStore } from './user'

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
  const userStore = useUserStore()
  
  // Getters
  const upperNavItems = computed(() => {
    const items: MenuItem[] = [
      {
        key: 'chat',
        label: '智能问答',
        icon: 'ChatDotRound',
        route: '/chat'
      },
      {
        key: 'smart-query',
        label: '智能问数',
        icon: 'DataAnalysis',
        route: '/smart-query'
      },
      {
        key: 'creation',
        label: '智能创作',
        icon: 'EditPen',
        route: '/creation'
      },
      {
        key: 'market',
        label: '智能体市场',
        icon: 'Shop',
        route: '/market'
      }
    ]
    
    return items
  })
  
  const lowerNavItems = computed(() => {
    const items: MenuItem[] = [
      {
        key: 'knowledge',
        label: '知识库',
        icon: 'Collection',
        route: '/knowledge'
      },
      {
        key: 'workflow',
        label: '工作流编排',
        icon: 'Connection',
        route: '/workflow'
      },
      {
        key: 'agent',
        label: '智能体管理',
        icon: 'Cpu',
        route: '/agent'
      }
    ]
    
    // 如果是超级管理员，添加系统管理菜单
    if (userStore.user?.is_superuser) {
      items.push({
        key: 'system',
        label: '系统管理',
        icon: 'Setting',
        route: '/system',
        expandable: true,
        children: [
          {
            key: 'users',
            label: '用户管理',
            icon: 'User',
            route: '/system/users'
          },
          {
            key: 'roles',
            label: '角色管理',
            icon: 'UserFilled',
            route: '/system/roles'
          },
          {
            key: 'llm-configs',
            label: '大模型管理',
            icon: 'Cpu',
            route: '/system/llm-configs'
          }
        ],
        requires_admin: true
      })
    }
    
    return items
  })
  
  return {
    // Getters
    upperNavItems,
    lowerNavItems
  }
})