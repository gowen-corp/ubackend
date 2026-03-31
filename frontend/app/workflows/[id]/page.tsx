'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

interface Workflow {
  id: number
  name: string
  trigger_event: string
  description?: string
  steps: any[]
  is_active: boolean
  created_at: string
}

interface WorkflowRun {
  id: number
  workflow_id: number
  status: string
  context: any
  current_step: number
  error_message?: string
  started_at: string
  completed_at?: string
}

export default function WorkflowDetailPage() {
  const params = useParams()
  const router = useRouter()
  const workflowId = parseInt(params.id as string)
  
  const [workflow, setWorkflow] = useState<Workflow | null>(null)
  const [runs, setRuns] = useState<WorkflowRun[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isTriggering, setIsTriggering] = useState(false)
  
  const loadWorkflow = async () => {
    try {
      setIsLoading(true)
      const [workflowRes, runsRes] = await Promise.all([
        fetch(`/api/v1/workflows/${workflowId}`),
        fetch(`/api/v1/workflows/${workflowId}/runs?limit=10`),
      ])
      
      const workflowData = await workflowRes.json()
      const runsData = await runsRes.json()
      
      setWorkflow(workflowData)
      setRuns(runsData)
    } catch (e) {
      console.error('Failed to load workflow:', e)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadWorkflow()
  }, [workflowId])
  
  const handleTrigger = async () => {
    if (!confirm('Run this workflow manually?')) return
    
    setIsTriggering(true)
    try {
      const response = await fetch(`/api/v1/workflows/${workflowId}/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      
      if (!response.ok) throw new Error('Failed to trigger workflow')
      
      // Reload runs after triggering
      setTimeout(loadWorkflow, 1000)
    } catch (e: any) {
      alert(e.message)
    } finally {
      setIsTriggering(false)
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading workflow...</p>
      </div>
    )
  }
  
  if (!workflow) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Workflow not found</p>
          <Button variant="outline" className="mt-4" asChild>
            <Link href="/workflows">Back to Workflows</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{workflow.name}</h1>
          <p className="text-muted-foreground">{workflow.description || 'No description'}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="default"
            onClick={handleTrigger}
            disabled={isTriggering || !workflow.is_active}
          >
            {isTriggering ? 'Running...' : '▶ Run Now'}
          </Button>
          <Button variant="outline" asChild>
            <Link href={`/workflows/${workflowId}/edit`}>Edit</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/workflows">Back to Workflows</Link>
          </Button>
        </div>
      </div>
      
      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                workflow.is_active
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {workflow.is_active ? 'Active' : 'Inactive'}
            </span>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Trigger
            </CardTitle>
          </CardHeader>
          <CardContent>
            <code className="text-sm font-mono">{workflow.trigger_event}</code>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{workflow.steps.length}</span>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Runs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{runs.length}</span>
          </CardContent>
        </Card>
      </div>
      
      {/* Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Steps</CardTitle>
        </CardHeader>
        <CardContent>
          {workflow.steps.length === 0 ? (
            <p className="text-muted-foreground">No steps defined</p>
          ) : (
            <div className="space-y-2">
              {workflow.steps.map((step, index) => (
                <div
                  key={index}
                  className="flex items-center gap-4 p-3 border rounded-lg"
                >
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <p className="font-medium">{step.name || step.type}</p>
                    <p className="text-sm text-muted-foreground">{step.type}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Execution History */}
      <Card>
        <CardHeader>
          <CardTitle>Execution History</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <p className="text-muted-foreground">No executions yet</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Completed</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-mono text-sm">#{run.id}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          run.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : run.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {run.status}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">
                      {new Date(run.started_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm">
                      {run.completed_at
                        ? new Date(run.completed_at).toLocaleString()
                        : '—'}
                    </TableCell>
                    <TableCell className="text-sm">
                      {run.completed_at
                        ? `${((new Date(run.completed_at).getTime() -
                            new Date(run.started_at).getTime()) /
                            1000).toFixed(1)}s`
                        : 'Running...'}
                    </TableCell>
                    <TableCell className="max-w-xs truncate text-sm text-destructive">
                      {run.error_message || '—'}
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
