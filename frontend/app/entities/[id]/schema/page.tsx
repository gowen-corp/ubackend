'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { entitiesApi } from '@/lib/api'
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
import Link from 'next/link'

interface SchemaField {
  name: string
  type: string
  required: boolean
  description?: string
}

const FIELD_TYPES = [
  { value: 'string', label: 'String' },
  { value: 'text', label: 'Text (Long)' },
  { value: 'number', label: 'Number' },
  { value: 'integer', label: 'Integer' },
  { value: 'boolean', label: 'Boolean' },
  { value: 'date', label: 'Date' },
  { value: 'datetime', label: 'DateTime' },
  { value: 'email', label: 'Email' },
  { value: 'json', label: 'JSON' },
  { value: 'array', label: 'Array' },
  { value: 'reference', label: 'Reference' },
]

export default function EntitySchemaPage() {
  const params = useParams()
  const router = useRouter()
  const entityId = parseInt(params.id as string)
  
  const [entity, setEntity] = useState<any>(null)
  const [fields, setFields] = useState<SchemaField[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  
  // New field form
  const [newFieldName, setNewFieldName] = useState('')
  const [newFieldType, setNewFieldType] = useState('string')
  const [newFieldRequired, setNewFieldRequired] = useState(false)
  const [newFieldDescription, setNewFieldDescription] = useState('')
  
  const loadEntity = async () => {
    try {
      setIsLoading(true)
      const response = await entitiesApi.get(entityId)
      const entityData = response.data
      setEntity(entityData)
      
      // Parse fields from schema
      const schema = entityData.schema || { properties: {}, required: [] }
      const parsedFields: SchemaField[] = []
      
      Object.entries(schema.properties || {}).forEach(([name, props]: [string, any]) => {
        parsedFields.push({
          name,
          type: props.type || 'string',
          required: schema.required?.includes(name) || false,
          description: props.description,
        })
      })
      
      setFields(parsedFields)
    } catch (e: any) {
      console.error('Failed to load entity:', e)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadEntity()
  }, [entityId])
  
  const handleAddField = async () => {
    if (!newFieldName.trim()) {
      alert('Field name is required')
      return
    }
    
    if (fields.some(f => f.name === newFieldName)) {
      alert('Field with this name already exists')
      return
    }
    
    setIsSaving(true)
    try {
      // Optimistic update
      const newField: SchemaField = {
        name: newFieldName,
        type: newFieldType,
        required: newFieldRequired,
        description: newFieldDescription || undefined,
      }
      
      setFields([...fields, newField])
      
      // Rebuild schema and save
      const schema = buildSchemaFromFields([...fields, newField])
      await entitiesApi.update(entityId, { schema })
      
      // Reset form
      setNewFieldName('')
      setNewFieldType('string')
      setNewFieldRequired(false)
      setNewFieldDescription('')
    } catch (e: any) {
      alert('Failed to add field')
      console.error(e)
      // Rollback
      setFields(fields)
    } finally {
      setIsSaving(false)
    }
  }
  
  const handleRemoveField = async (fieldName: string) => {
    if (!confirm(`Remove field "${fieldName}"?`)) return
    
    setIsSaving(true)
    try {
      const newFields = fields.filter(f => f.name !== fieldName)
      setFields(newFields)
      
      const schema = buildSchemaFromFields(newFields)
      await entitiesApi.update(entityId, { schema })
    } catch (e: any) {
      alert('Failed to remove field')
      console.error(e)
      setFields(fields)
    } finally {
      setIsSaving(false)
    }
  }
  
  const buildSchemaFromFields = (fieldsList: SchemaField[]) => {
    const properties: Record<string, any> = {}
    const required: string[] = []
    
    fieldsList.forEach(field => {
      properties[field.name] = {
        type: field.type,
        ...(field.description && { description: field.description }),
      }
      
      if (field.required) {
        required.push(field.name)
      }
    })
    
    return {
      type: 'object',
      properties,
      required,
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading schema...</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Schema Builder</h1>
          <p className="text-muted-foreground">
            Manage fields for &quot;{entity?.name}&quot;
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href={`/entities/${entityId}`}>Back to Entity</Link>
        </Button>
      </div>
      
      {/* Add Field Form */}
      <Card>
        <CardHeader>
          <CardTitle>Add New Field</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-12 gap-4 items-end">
            <div className="col-span-3 space-y-2">
              <label className="text-sm font-medium">Field Name</label>
              <Input
                placeholder="e.g., email, age, status"
                value={newFieldName}
                onChange={(e) => setNewFieldName(e.target.value)}
                disabled={isSaving}
              />
            </div>
            
            <div className="col-span-2 space-y-2">
              <label className="text-sm font-medium">Type</label>
              <select
                value={newFieldType}
                onChange={(e) => setNewFieldType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                disabled={isSaving}
              >
                {FIELD_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="col-span-3 space-y-2">
              <label className="text-sm font-medium">Description</label>
              <Input
                placeholder="Field description"
                value={newFieldDescription}
                onChange={(e) => setNewFieldDescription(e.target.value)}
                disabled={isSaving}
              />
            </div>
            
            <div className="col-span-2 flex items-center space-x-2 pb-2">
              <input
                type="checkbox"
                id="required"
                checked={newFieldRequired}
                onChange={(e) => setNewFieldRequired(e.target.checked)}
                disabled={isSaving}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="required" className="text-sm font-medium">
                Required
              </label>
            </div>
            
            <div className="col-span-2">
              <Button onClick={handleAddField} disabled={isSaving || !newFieldName}>
                {isSaving ? 'Saving...' : 'Add Field'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Fields Table */}
      <Card>
        <CardHeader>
          <CardTitle>Fields ({fields.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {fields.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No fields defined yet</p>
              <p className="text-sm">Add your first field using the form above</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Required</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fields.map((field) => (
                  <TableRow key={field.name}>
                    <TableCell className="font-mono">{field.name}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {field.type}
                      </span>
                    </TableCell>
                    <TableCell>
                      {field.required ? (
                        <span className="text-red-600 font-medium">Yes</span>
                      ) : (
                        <span className="text-muted-foreground">No</span>
                      )}
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {field.description || '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveField(field.name)}
                        disabled={isSaving}
                      >
                        Remove
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      
      {/* JSON Preview */}
      <Card>
        <CardHeader>
          <CardTitle>JSON Schema Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded-md overflow-auto max-h-64 text-sm font-mono">
            {JSON.stringify(buildSchemaFromFields(fields), null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}
