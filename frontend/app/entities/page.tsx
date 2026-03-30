'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { entitiesApi, type Entity } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const loadEntities = async () => {
    try {
      setIsLoading(true)
      const response = await entitiesApi.list()
      setEntities(response.data)
      setError(null)
    } catch (e: any) {
      setError('Failed to load entities')
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadEntities()
  }, [])
  
  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this entity?')) return
    
    try {
      await entitiesApi.delete(id)
      setEntities(entities.filter((e) => e.id !== id))
    } catch (e: any) {
      alert('Failed to delete entity')
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading entities...</p>
      </div>
    )
  }
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Entities</CardTitle>
        <Button asChild>
          <Link href="/entities/new">Create Entity</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="p-4 text-destructive bg-destructive/10 rounded-md">
            {error}
            <Button
              variant="outline"
              size="sm"
              onClick={loadEntities}
              className="ml-4"
            >
              Retry
            </Button>
          </div>
        ) : entities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No entities yet</p>
            <Button variant="link" asChild>
              <Link href="/entities/new">Create your first entity</Link>
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entities.map((entity) => (
                <TableRow key={entity.id}>
                  <TableCell className="font-mono text-sm">{entity.id}</TableCell>
                  <TableCell className="font-medium">{entity.name}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {entity.description || '—'}
                  </TableCell>
                  <TableCell className="font-mono text-sm">{entity.version}</TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        entity.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {entity.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                    >
                      <Link href={`/entities/${entity.id}`}>View</Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                    >
                      <Link href={`/entities/${entity.id}/edit`}>Edit</Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(entity.id)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
