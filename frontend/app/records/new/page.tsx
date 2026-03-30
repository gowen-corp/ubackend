'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm, useFieldArray } from 'react-hook-form'
import { recordsApi, entitiesApi, type Entity } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'

interface RecordForm {
  data: Record<string, any>
}

export default function NewRecordPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [entity, setEntity] = useState<Entity | null>(null)
  const [dynamicFields, setDynamicFields] = useState<Array<{ name: string; type: string }>>([])
  
  const entityId = parseInt(searchParams.get('entity_id') || '0')
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<RecordForm>({
    defaultValues: {
      data: {},
    },
  })
  
  // Загрузка сущности
  useEffect(() => {
    if (!entityId) return
    
    const loadEntity = async () => {
      try {
        const response = await entitiesApi.get(entityId)
        setEntity(response.data)
        
        // Генерируем поля из schema если есть
        const schema = response.data.schema
        if (schema?.properties) {
          const fields = Object.entries(schema.properties).map(([name, prop]: [string, any]) => ({
            name,
            type: prop.type || 'string',
          }))
          setDynamicFields(fields)
        }
      } catch (e: any) {
        console.error('Failed to load entity:', e)
      }
    }
    
    loadEntity()
  }, [entityId])
  
  const onSubmit = async (data: RecordForm) => {
    setIsLoading(true)
    setError(null)
    
    try {
      await recordsApi.create({
        entity_id: entityId,
        data: data.data,
      })
      router.push('/records')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to create record')
    } finally {
      setIsLoading(false)
    }
  }
  
  // Рендер поля ввода в зависимости от типа
  const renderField = (fieldName: string, fieldType: string) => {
    const fieldKey = `data.${fieldName}`
    
    switch (fieldType) {
      case 'integer':
      case 'number':
        return (
          <Input
            type="number"
            {...register(fieldKey as any, { valueAsNumber: true })}
            placeholder={`Enter ${fieldName}`}
          />
        )
      
      case 'boolean':
        return (
          <select
            {...register(fieldKey as any, { valueAsNumber: false })}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select...</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        )
      
      case 'string':
      default:
        return (
          <Input
            type="text"
            {...register(fieldKey as any)}
            placeholder={`Enter ${fieldName}`}
          />
        )
    }
  }
  
  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Create New Record</CardTitle>
        <CardDescription>
          {entity ? `Adding record to "${entity.name}"` : 'Loading entity...'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Динамические поля из schema */}
          {dynamicFields.length > 0 ? (
            dynamicFields.map((field) => (
              <div key={field.name} className="space-y-2">
                <Label htmlFor={field.name} className="capitalize">
                  {field.name}
                  {field.type !== 'string' && (
                    <span className="text-muted-foreground text-xs ml-2">
                      ({field.type})
                    </span>
                  )}
                </Label>
                {renderField(field.name, field.type)}
              </div>
            ))
          ) : (
            <div className="space-y-2">
              <Label>JSON Data</Label>
              <textarea
                {...register('data' as any)}
                className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
                placeholder='{"key": "value"}'
              />
              <p className="text-xs text-muted-foreground">
                Enter raw JSON data for this record
              </p>
            </div>
          )}
          
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}
          
          <div className="flex gap-4">
            <Button type="submit" disabled={isLoading || !entityId}>
              {isLoading ? 'Creating...' : 'Create Record'}
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
