'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuthStore } from '@/store/authStore'
import { entitiesApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export default function Home() {
  const { isAuthenticated, user, checkAuth } = useAuthStore()
  const [entityCount, setEntityCount] = useState(0)
  
  useEffect(() => {
    checkAuth()
    
    // Загружаем количество сущностей
    entitiesApi.list().then((res) => {
      setEntityCount(res.data.length)
    }).catch(() => {})
  }, [])
  
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Welcome to uBackend Studio
            {isAuthenticated && `, ${user?.username}!`}
          </h1>
          <p className="text-muted-foreground mt-1">
            Low-Code Platform for Internal Tools
          </p>
        </div>
        {!isAuthenticated && (
          <Button asChild>
            <Link href="/login">Sign In</Link>
          </Button>
        )}
      </div>
      
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Entities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{entityCount}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <Link href="/entities" className="hover:underline">
                View all →
              </Link>
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
            <div className="text-3xl font-bold">—</div>
            <p className="text-xs text-muted-foreground mt-1">
              Coming soon
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
            <div className="text-3xl font-bold">—</div>
            <p className="text-xs text-muted-foreground mt-1">
              Coming soon
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
          <CardDescription>
            Get started with your low-code platform
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="border rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">1. Create an Entity</h3>
            <p className="text-sm text-muted-foreground">
              Define your data model by creating a new entity
            </p>
            <Button size="sm" asChild>
              <Link href="/entities/new">Create Entity</Link>
            </Button>
          </div>
          
          <div className="border rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">2. Add Records</h3>
            <p className="text-sm text-muted-foreground">
              Start adding data records to your entity
            </p>
            <Button size="sm" variant="outline" asChild>
              <Link href="/records">View Records</Link>
            </Button>
          </div>
          
          <div className="border rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">3. Configure Workflows</h3>
            <p className="text-sm text-muted-foreground">
              Automate your business processes
            </p>
            <Button size="sm" variant="outline" disabled>
              Coming Soon
            </Button>
          </div>
          
          <div className="border rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">4. API Documentation</h3>
            <p className="text-sm text-muted-foreground">
              Explore the REST API
            </p>
            <Button size="sm" variant="outline" asChild>
              <a href="/api/v1/docs" target="_blank">Open Swagger</a>
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">API Connection</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Authentication</span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  isAuthenticated
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {isAuthenticated ? 'Authenticated' : 'Not Logged In'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
