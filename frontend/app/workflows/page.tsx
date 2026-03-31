'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
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

interface Workflow {
  id: number
  name: string
  trigger_event: string
  description?: string
  steps: any[]
  is_active: boolean
  created_at: string
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  
  const loadWorkflows = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/workflows')
      const data = await response.json()
      
      // Проверяем что данные это массив
      if (Array.isArray(data)) {
        setWorkflows(data)
      } else {
        console.error('Workflows data is not an array:', data)
        setWorkflows([])
      }
    } catch (e) {
      console.error('Failed to load workflows:', e)
      setWorkflows([])
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadWorkflows()
  }, [])
  
  const handleToggle = async (id: number) => {
    try {
      await fetch(`/api/v1/workflows/${id}/toggle`, { method: 'POST' })
      setWorkflows(workflows.map(w => 
        w.id === id ? { ...w, is_active: !w.is_active } : w
      ))
    } catch (e) {
      alert('Failed to toggle workflow')
    }
  }
  
  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return
    
    try {
      await fetch(`/api/v1/workflows/${id}`, { method: 'DELETE' })
      setWorkflows(workflows.filter(w => w.id !== id))
    } catch (e) {
      alert('Failed to delete workflow')
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading workflows...</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workflows</h1>
          <p className="text-muted-foreground">Automate your business processes</p>
        </div>
        <Button asChild>
          <Link href="/workflows/new">Create Workflow</Link>
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Workflows ({workflows.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {workflows.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No workflows yet</p>
              <Button variant="link" asChild>
                <Link href="/workflows/new">Create your first workflow</Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Trigger Event</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflows.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell className="font-medium">{workflow.name}</TableCell>
                    <TableCell className="font-mono text-sm">{workflow.trigger_event}</TableCell>
                    <TableCell>{workflow.steps.length}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          workflow.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {workflow.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(workflow.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/workflows/${workflow.id}`}>View</Link>
                      </Button>
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/workflows/${workflow.id}/edit`}>Edit</Link>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggle(workflow.id)}
                      >
                        {workflow.is_active ? 'Disable' : 'Enable'}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(workflow.id)}
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
    </div>
  )
}
