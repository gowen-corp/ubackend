'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { entitiesApi, type Entity } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function EntityDetailPage() {
  const params = useParams()
  const router = useRouter()
  const entityId = parseInt(params.id as string)
  
  const [entity, setEntity] = useState<Entity | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    const loadEntity = async () => {
      try {
        setIsLoading(true)
        const response = await entitiesApi.get(entityId)
        setEntity(response.data)
        setError(null)
      } catch (e: any) {
        setError('Failed to load entity')
        console.error(e)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadEntity()
  }, [entityId])
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading entity...</p>
      </div>
    )
  }
  
  if (error || !entity) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || 'Entity not found'}</p>
          <Button variant="outline" className="mt-4" asChild>
            <Link href="/entities">Back to Entities</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }
  
  const fieldCount = entity.schema?.properties 
    ? Object.keys(entity.schema.properties).length 
    : 0
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{entity.name}</h1>
          <p className="text-muted-foreground">
            {entity.description || 'No description'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/entities/${entityId}/schema`}>
              Schema Builder
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href={`/entities/${entityId}/edit`}>
              Edit
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/entities">
              Back to Entities
            </Link>
          </Button>
        </div>
      </div>
      
      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Fields
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{fieldCount}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Version
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{entity.version}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                entity.is_active
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {entity.is_active ? 'Active' : 'Inactive'}
            </span>
          </CardContent>
        </Card>
      </div>
      
      {/* Schema Preview */}
      {entity.schema && Object.keys(entity.schema).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Schema</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-md overflow-auto max-h-96 text-sm font-mono">
              {JSON.stringify(entity.schema, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
      
      {/* Meta */}
      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Created:</span>
              <span className="ml-2">
                {new Date(entity.created_at).toLocaleString()}
              </span>
            </div>
            {entity.updated_at && (
              <div>
                <span className="text-muted-foreground">Updated:</span>
                <span className="ml-2">
                  {new Date(entity.updated_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
