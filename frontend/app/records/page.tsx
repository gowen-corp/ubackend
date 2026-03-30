'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { recordsApi, entitiesApi, type Record, type Entity } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function RecordsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [records, setRecords] = useState<Record[]>([])
  const [entities, setEntities] = useState<Entity[]>([])
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Pagination
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  
  // Filters
  const [filterField, setFilterField] = useState('')
  const [filterValue, setFilterValue] = useState('')
  
  // Загрузка сущностей для селектора
  useEffect(() => {
    const loadEntities = async () => {
      try {
        const response = await entitiesApi.list()
        setEntities(response.data)
        
        // Выбираем первую сущность или ту, что в URL
        const entityIdParam = searchParams.get('entity_id')
        if (entityIdParam) {
          setSelectedEntityId(parseInt(entityIdParam))
        } else if (response.data.length > 0) {
          setSelectedEntityId(response.data[0].id)
        }
      } catch (e: any) {
        console.error('Failed to load entities:', e)
      }
    }
    
    loadEntities()
  }, [])
  
  // Загрузка записей при изменении сущности или фильтров
  useEffect(() => {
    if (!selectedEntityId) return
    
    const loadRecords = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        // Строим фильтры
        const filters: Record<string, any> = {}
        if (filterField && filterValue) {
          filters[filterField] = { contains: filterValue }
        }
        
        const response = await recordsApi.list(
          selectedEntityId,
          Object.keys(filters).length > 0 ? filters : undefined,
          page,
          pageSize
        )
        
        setRecords(response.data.items)
        setTotalPages(response.data.total_pages)
        setTotal(response.data.total)
      } catch (e: any) {
        setError('Failed to load records')
        console.error(e)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadRecords()
  }, [selectedEntityId, page, filterField, filterValue])
  
  const handleEntityChange = (entityId: number) => {
    setSelectedEntityId(entityId)
    setPage(1)
    router.push(`/records?entity_id=${entityId}`, { scroll: false })
  }
  
  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this record?')) return
    
    try {
      await recordsApi.delete(id)
      setRecords(records.filter((r) => r.id !== id))
    } catch (e: any) {
      alert('Failed to delete record')
    }
  }
  
  // Получаем поля из первой записи для динамических колонок
  const dynamicFields = records.length > 0 
    ? Object.keys(records[0].data).slice(0, 5) // Показываем первые 5 полей
    : []
  
  if (!selectedEntityId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Records</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p>No entities available</p>
            <Button variant="link" asChild>
              <Link href="/entities/new">Create your first entity</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <div className="space-y-4">
      {/* Header with entity selector */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Records</CardTitle>
          <div className="flex items-center gap-4">
            <select
              value={selectedEntityId}
              onChange={(e) => handleEntityChange(parseInt(e.target.value))}
              className="h-10 px-3 py-2 border rounded-md bg-background text-sm"
            >
              {entities.map((entity) => (
                <option key={entity.id} value={entity.id}>
                  {entity.name}
                </option>
              ))}
            </select>
            <Button asChild>
              <Link href={`/records/new?entity_id=${selectedEntityId}`}>
                Create Record
              </Link>
            </Button>
          </div>
        </CardHeader>
      </Card>
      
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Filter by field</label>
              <Input
                placeholder="Field name (e.g., status, name)"
                value={filterField}
                onChange={(e) => setFilterField(e.target.value)}
              />
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Contains value</label>
              <Input
                placeholder="Search value"
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
              />
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setFilterField('')
                setFilterValue('')
              }}
            >
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Records Table */}
      <Card>
        <CardContent className="pt-6">
          {error ? (
            <div className="p-4 text-destructive bg-destructive/10 rounded-md">
              {error}
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
                className="ml-4"
              >
                Retry
              </Button>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center h-32">
              <p className="text-muted-foreground">Loading records...</p>
            </div>
          ) : records.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No records found</p>
              <Button variant="link" asChild>
                <Link href={`/records/new?entity_id=${selectedEntityId}`}>
                  Create your first record
                </Link>
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">ID</TableHead>
                    {dynamicFields.map((field) => (
                      <TableHead key={field} className="capitalize">
                        {field}
                      </TableHead>
                    ))}
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-mono text-sm">
                        {record.id}
                      </TableCell>
                      {dynamicFields.map((field) => (
                        <TableCell key={field} className="max-w-xs truncate">
                          {typeof record.data[field] === 'object'
                            ? JSON.stringify(record.data[field])
                            : String(record.data[field] ?? '—')}
                        </TableCell>
                      ))}
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(record.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          asChild
                        >
                          <Link href={`/records/${record.id}`}>View</Link>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          asChild
                        >
                          <Link href={`/records/${record.id}/edit`}>Edit</Link>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(record.id)}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  Showing {records.length} of {total} records
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="flex items-center px-4 text-sm">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
