'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { entitiesApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

interface EntityForm {
  name: string
  description: string
}

export default function NewEntityPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EntityForm>()
  
  const onSubmit = async (data: EntityForm) => {
    setIsLoading(true)
    setError(null)
    
    try {
      await entitiesApi.create({
        name: data.name,
        description: data.description || undefined,
        schema: {},
      })
      router.push('/entities')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to create entity')
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Create New Entity</CardTitle>
        <CardDescription>
          Define a new entity type to store your data
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <label
              htmlFor="name"
              className="text-sm font-medium leading-none"
            >
              Name *
            </label>
            <Input
              id="name"
              type="text"
              placeholder="e.g., users, orders, products"
              {...register('name', {
                required: 'Name is required',
                pattern: {
                  value: /^[a-z_][a-z0-9_]*$/,
                  message: 'Use lowercase letters, numbers, and underscores only',
                },
              })}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>
          
          <div className="space-y-2">
            <label
              htmlFor="description"
              className="text-sm font-medium leading-none"
            >
              Description
            </label>
            <Input
              id="description"
              type="text"
              placeholder="Brief description of this entity"
              {...register('description')}
            />
          </div>
          
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}
          
          <div className="flex gap-4">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Entity'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
