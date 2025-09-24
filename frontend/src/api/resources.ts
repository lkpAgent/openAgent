import request from './request'

// 资源相关接口
export interface Resource {
  id: number
  name: string
  code: string
  type: 'menu' | 'button' | 'api'
  path?: string
  component?: string
  icon?: string
  description?: string
  parent_id?: number
  sort_order: number
  requires_auth: boolean
  requires_admin: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  children?: Resource[]
}

export interface ResourceCreate {
  name: string
  code: string
  type: 'menu' | 'button' | 'api'
  path?: string
  component?: string
  icon?: string
  description?: string
  parent_id?: number
  sort_order: number
  requires_auth: boolean
  requires_admin: boolean
}

export interface ResourceUpdate {
  name?: string
  code?: string
  type?: 'menu' | 'button' | 'api'
  path?: string
  component?: string
  icon?: string
  description?: string
  parent_id?: number
  sort_order?: number
  requires_auth?: boolean
  requires_admin?: boolean
  is_active?: boolean
}

export interface ResourceTreeNode {
  id: number
  name: string
  code: string
  type: 'menu' | 'button' | 'api'
  path?: string
  icon?: string
  requires_auth: boolean
  requires_admin: boolean
  children?: ResourceTreeNode[]
}

export interface RoleResourceAssign {
  role_id: number
  resource_ids: number[]
}

export interface RoleResource {
  id: number
  role_id: number
  resource_id: number
  resource: Resource
}

export interface GetResourcesParams {
  page?: number
  size?: number
  search?: string
  type?: string
  parent_id?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

// 资源管理API
export const resourcesApi = {
  // 获取资源列表
  getResources: (params?: GetResourcesParams) => {
    return request.get<PaginatedResponse<Resource>>('/admin/resources/', { params })
  },

  // 获取资源树
  getResourceTree: () => {
    return request.get<ResourceTreeNode[]>('/admin/resources/tree/')
  },

  // 获取资源详情
  getResource: (id: number) => {
    return request.get<Resource>(`/admin/resources/${id}/`)
  },

  // 创建资源
  createResource: (data: ResourceCreate) => {
    return request.post<Resource>('/admin/resources/', data)
  },

  // 更新资源
  updateResource: (id: number, data: ResourceUpdate) => {
    return request.put<Resource>(`/admin/resources/${id}`, data)
  },

  // 删除资源
  deleteResource: (id: number) => {
    return request.delete(`/admin/resources/${id}`)
  },

  // 分配角色资源
  assignRoleResources: (data: RoleResourceAssign) => {
    return request.post('/admin/resources/assign-role/', data)
  },

  // 获取当前用户可访问的菜单资源
  getUserMenuResources: () => {
    return request.get<ResourceTreeNode[]>('/admin/resources/user/menu')
  },

  // 获取角色资源列表
  getRoleResources: (roleId: number) => {
    return request.get<RoleResource[]>(`/admin/resources/role/${roleId}/`)
  },

  // 批量删除资源
  batchDeleteResources: (resourceIds: number[]) => {
    return request.delete('/admin/resources/batch/', {
      data: { resource_ids: resourceIds }
    })
  },

  // 批量更新资源状态
  batchUpdateResourceStatus: (resourceIds: number[], isActive: boolean) => {
    return request.put('/admin/resources/batch/status/', {
      resource_ids: resourceIds,
      is_active: isActive
    })
  }
}