'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

interface Role {
  id: number
  name: string
  description?: string
  permissions: string[]
  is_system: boolean
  created_at: string
}

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  
  // New role form
  const [newRoleName, setNewRoleName] = useState('')
  const [newRoleDescription, setNewRoleDescription] = useState('')
  
  const loadRoles = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/rbac/roles')
      const data = await response.json()
      setRoles(data)
    } catch (e) {
      console.error('Failed to load roles:', e)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadRoles()
  }, [])
  
  const handleCreateRole = async () => {
    if (!newRoleName.trim()) {
      alert('Role name is required')
      return
    }
    
    setIsCreating(true)
    try {
      const response = await fetch('/api/v1/rbac/roles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newRoleName,
          description: newRoleDescription || undefined,
          permissions: [],
        }),
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail)
      }
      
      await loadRoles()
      setNewRoleName('')
      setNewRoleDescription('')
    } catch (e: any) {
      alert(`Failed to create role: ${e.message}`)
    } finally {
      setIsCreating(false)
    }
  }
  
  const handleDeleteRole = async (roleId: number, isSystem: boolean) => {
    if (isSystem) {
      alert('Cannot delete system role')
      return
    }
    
    if (!confirm('Are you sure you want to delete this role?')) return
    
    try {
      const response = await fetch(`/api/v1/rbac/roles/${roleId}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail)
      }
      
      await loadRoles()
    } catch (e: any) {
      alert(`Failed to delete role: ${e.message}`)
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading roles...</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Roles Management</h1>
        <p className="text-muted-foreground">Manage user roles and permissions</p>
      </div>
      
      {/* Create Role Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Role</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Role Name *</label>
              <Input
                placeholder="e.g., manager, editor"
                value={newRoleName}
                onChange={(e) => setNewRoleName(e.target.value)}
                disabled={isCreating}
              />
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Description</label>
              <Input
                placeholder="Role description"
                value={newRoleDescription}
                onChange={(e) => setNewRoleDescription(e.target.value)}
                disabled={isCreating}
              />
            </div>
            <Button onClick={handleCreateRole} disabled={isCreating || !newRoleName}>
              {isCreating ? 'Creating...' : 'Create Role'}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle>Roles ({roles.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {roles.map((role) => (
                <TableRow key={role.id}>
                  <TableCell className="font-medium">{role.name}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {role.description || '—'}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {role.permissions?.slice(0, 3).map((perm: string) => (
                        <span
                          key={perm}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {perm}
                        </span>
                      ))}
                      {role.permissions?.length > 3 && (
                        <span className="text-xs text-muted-foreground">
                          +{role.permissions.length - 3} more
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {role.is_system ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        System
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Custom
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(role.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteRole(role.id, role.is_system)}
                      disabled={role.is_system}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
