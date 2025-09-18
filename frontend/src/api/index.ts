// Export all API modules
export { authApi } from './auth'
export { usersApi } from './users'
export { chatApi } from './chat'
export { knowledgeApi } from './knowledge'
export { rolesApi } from './roles'
export { departmentsApi } from './departments'
export { userDepartmentsApi } from './userDepartments'
export { api } from './request'

// Re-export request instance as default
export { default } from './request'