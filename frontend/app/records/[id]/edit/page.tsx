'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { recordsApi, type Record } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import Link from 'next/link'

interface RecordForm {
  data: Record<string, any>
}

export default function EditRecordPage() {
  const params = useParams()
  const router = useRouter()
  const recordId = parseInt(params.id as string)
  
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [record, setRecord] = useState<Record | null>(null)
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<RecordForm>({
    defaultValues: {
      data: {},
    },
  })
  
  // Загрузка записи
  useEffect(() => {
    const loadRecord = async () => {
      try {
        setIsFetching(true)
        const response = await recordsApi.get(recordId)
        setRecord(response.data)
        reset({ data: response.data.data })
      } catch (e: any) {
        setError('Failed to load record')
        console.error(e)
      } finally {
        setIsFetching(false)
      }
    }
    
    loadRecord()
  }, [recordId, reset])
  
  const onSubmit = async (data: RecordForm) => {
    setIsLoading(true)
    setError(null)
    
    try {
      await recordsApi.update(recordId, { data: data.data })
      router.push(`/records/${recordId}`)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to update record')
    } finally {
      setIsLoading(false)
    }
  }
  
  if (isFetching) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading record...</p>
      </div>
    )
  }
  
  if (!record) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Record not found</p>
          <Button variant="outline" className="mt-4" asChild>
            <Link href="/records">Back to Records</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Edit Record</CardTitle>
        <CardDescription>
          Updating record #{record.id}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Динамические поля из данных */}
          {Object.keys(record.data).map((key) => {
            const value = record.data[key]
            const type = typeof value
            
            return (
              <div key={key} className="space-y-2">
                <Label htmlFor={key} className="capitalize">
                  {key}
                </Label>
                
                {type === 'boolean' ? (
                  <select
                    {...register(`data.${key}` as any)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                ) : type === 'number' ? (
                  <Input
                    type="number"
                    {...register(`data.${key}` as any, { valueAsNumber: true })}
                    defaultValue={value}
                  />
                ) : type === 'object' ? (
                  <textarea
                    {...register(`data.${key}` as any)}
                    className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
                    defaultValue={JSON.stringify(value, null, 2)}
                  />
                ) : (
                  <Input
                    type="text"
                    {...register(`data.${key}` as any)}
                    defaultValue={value}
                  />
                )}
              </div>
            )
          })}
          
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}
          
          <div className="flex gap-4">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Changes'}
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
