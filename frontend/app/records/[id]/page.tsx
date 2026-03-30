'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { recordsApi, type Record } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function RecordViewPage() {
  const params = useParams()
  const router = useRouter()
  const recordId = parseInt(params.id as string)
  
  const [record, setRecord] = useState<Record | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    const loadRecord = async () => {
      try {
        setIsLoading(true)
        const response = await recordsApi.get(recordId)
        setRecord(response.data)
        setError(null)
      } catch (e: any) {
        setError('Failed to load record')
        console.error(e)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadRecord()
  }, [recordId])
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading record...</p>
      </div>
    )
  }
  
  if (error || !record) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || 'Record not found'}</p>
          <Button variant="outline" className="mt-4" asChild>
            <Link href="/records">Back to Records</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Record #{record.id}</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" asChild>
                <Link href={`/records/${record.id}/edit`}>Edit</Link>
              </Button>
              <Button variant="outline" size="sm" asChild>
                <Link href="/records">Back to Records</Link>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">ID</p>
                <p className="font-mono">{record.id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Entity ID</p>
                <p className="font-mono">{record.entity_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Created</p>
                <p>{new Date(record.created_at).toLocaleString()}</p>
              </div>
              {record.updated_at && (
                <div>
                  <p className="text-sm text-muted-foreground">Updated</p>
                  <p>{new Date(record.updated_at).toLocaleString()}</p>
                </div>
              )}
            </div>
            
            <div className="border-t pt-4">
              <h3 className="font-semibold mb-2">Data</h3>
              <pre className="bg-muted p-4 rounded-md overflow-auto max-h-96">
                <code className="text-sm font-mono">
                  {JSON.stringify(record.data, null, 2)}
                </code>
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
