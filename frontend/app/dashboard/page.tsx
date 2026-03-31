'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

interface DashboardStats {
  entities_count: number
  records_count: number
  workflows_count: number
  users_count: number
  recent_activities: Activity[]
}

interface Activity {
  id: number
  action: string
  entity?: string
  user?: string
  timestamp: string
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [health, setHealth] = useState<any>(null)
  
  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setIsLoading(true)
        
        // Загружаем статистику
        const [entitiesRes, workflowsRes, healthRes] = await Promise.all([
          fetch('/api/v1/entities'),
          fetch('/api/v1/workflows'),
          fetch('/api/v1/health'),
        ])
        
        const entities = await entitiesRes.json()
        const workflows = await workflowsRes.json()
        const healthData = await healthRes.json()
        
        setStats({
          entities_count: entities.length,
          records_count: 0, // Нужно отдельное API
          workflows_count: workflows.length,
          users_count: 0,   // Нужно отдельное API
          recent_activities: [],
        })
        
        setHealth(healthData)
      } catch (e) {
        console.error('Failed to load dashboard:', e)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadDashboard()
  }, [])
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">System overview and metrics</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Entities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats?.entities_count || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Data models defined
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Records
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats?.records_count || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Total records stored
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Workflows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats?.workflows_count || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Active automations
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </span>
              <span className="text-lg font-semibold">
                {health?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Uptime: {health?.uptime_seconds ? `${Math.round(health.uptime_seconds / 60)} min` : 'N/A'}
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Uptime</p>
              <p className="text-lg font-semibold">
                {health?.uptime_seconds ? `${Math.round(health.uptime_seconds)}s` : 'N/A'}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Requests</p>
              <p className="text-lg font-semibold">
                {health?.total_requests || 0}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Errors</p>
              <p className="text-lg font-semibold">
                {health?.total_errors || 0}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Error Rate</p>
              <p className="text-lg font-semibold">
                {health?.error_rate || 0}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a
              href="/entities/new"
              className="p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <p className="font-semibold">Create Entity</p>
              <p className="text-sm text-muted-foreground">Add new data model</p>
            </a>
            <a
              href="/records"
              className="p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <p className="font-semibold">View Records</p>
              <p className="text-sm text-muted-foreground">Browse all data</p>
            </a>
            <a
              href="/workflows/new"
              className="p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <p className="font-semibold">Create Workflow</p>
              <p className="text-sm text-muted-foreground">Automate processes</p>
            </a>
            <a
              href="/admin/roles"
              className="p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <p className="font-semibold">Manage Roles</p>
              <p className="text-sm text-muted-foreground">Configure access</p>
            </a>
          </div>
        </CardContent>
      </Card>
      
      {/* Recent Activity Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            Activity logging will be implemented soon
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
