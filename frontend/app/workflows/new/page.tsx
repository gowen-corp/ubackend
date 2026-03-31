'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import Link from 'next/link'

const STEP_TYPES = [
  { value: 'http_request', label: 'HTTP Request', icon: '🌐' },
  { value: 'send_email', label: 'Send Email', icon: '📧' },
  { value: 'delay', label: 'Delay', icon: '⏱️' },
  { value: 'update_record', label: 'Update Record', icon: '✏️' },
  { value: 'create_record', label: 'Create Record', icon: '➕' },
  { value: 'trigger_event', label: 'Trigger Event', icon: '⚡' },
]

const TRIGGER_EVENTS = [
  { value: 'entity.created', label: 'Entity Created' },
  { value: 'entity.updated', label: 'Entity Updated' },
  { value: 'entity.deleted', label: 'Entity Deleted' },
  { value: 'record.created', label: 'Record Created' },
  { value: 'record.updated', label: 'Record Updated' },
  { value: 'record.deleted', label: 'Record Deleted' },
  { value: 'manual', label: 'Manual Trigger' },
]

interface Step {
  id: string
  type: string
  name: string
  config: Record<string, any>
}

export default function NewWorkflowPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Workflow data
  const [name, setName] = useState('')
  const [triggerEvent, setTriggerEvent] = useState('entity.created')
  const [description, setDescription] = useState('')
  const [steps, setSteps] = useState<Step[]>([])
  
  const addStep = () => {
    const newStep: Step = {
      id: `step-${Date.now()}`,
      type: 'http_request',
      name: 'New Step',
      config: {},
    }
    setSteps([...steps, newStep])
  }
  
  const removeStep = (stepId: string) => {
    setSteps(steps.filter(s => s.id !== stepId))
  }
  
  const updateStep = (stepId: string, updates: Partial<Step>) => {
    setSteps(steps.map(s => s.id === stepId ? { ...s, ...updates } : s))
  }
  
  const moveStep = (index: number, direction: 'up' | 'down') => {
    if ((direction === 'up' && index === 0) || 
        (direction === 'down' && index === steps.length - 1)) {
      return
    }
    
    const newSteps = [...steps]
    const newIndex = direction === 'up' ? index - 1 : index + 1
    ;[newSteps[index], newSteps[newIndex]] = [newSteps[newIndex], newSteps[index]]
    setSteps(newSteps)
  }
  
  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Workflow name is required')
      return
    }
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/v1/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          trigger_event: triggerEvent,
          description: description || undefined,
          steps: steps.map(({ id, ...step }) => step), // Remove internal id
        }),
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to create workflow')
      }
      
      router.push('/workflows')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Create Workflow</h1>
          <p className="text-muted-foreground">Define automation steps</p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/workflows">Cancel</Link>
        </Button>
      </div>
      
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}
      
      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Workflow Name *</Label>
            <Input
              id="name"
              placeholder="e.g., Send email on new record"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="trigger">Trigger Event *</Label>
            <select
              id="trigger"
              value={triggerEvent}
              onChange={(e) => setTriggerEvent(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TRIGGER_EVENTS.map((event) => (
                <option key={event.value} value={event.value}>
                  {event.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              placeholder="Brief description of what this workflow does"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>
      
      {/* Steps Editor */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Workflow Steps</CardTitle>
            <Button onClick={addStep} size="sm">
              + Add Step
            </Button>
          </div>
          <CardDescription>
            Steps will be executed in order when the trigger event occurs
          </CardDescription>
        </CardHeader>
        <CardContent>
          {steps.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
              <p className="text-lg mb-2">No steps yet</p>
              <p className="text-sm mb-4">Add your first step to get started</p>
              <Button onClick={addStep}>Add Step</Button>
            </div>
          ) : (
            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={step.id} className="border rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-muted-foreground">
                        #{index + 1}
                      </span>
                      <select
                        value={step.type}
                        onChange={(e) => updateStep(step.id, { type: e.target.value })}
                        className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                      >
                        {STEP_TYPES.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.icon} {type.label}
                          </option>
                        ))}
                      </select>
                      <Input
                        placeholder="Step name"
                        value={step.name}
                        onChange={(e) => updateStep(step.id, { name: e.target.value })}
                        className="w-48"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveStep(index, 'up')}
                        disabled={index === 0}
                      >
                        ↑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveStep(index, 'down')}
                        disabled={index === steps.length - 1}
                      >
                        ↓
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeStep(step.id)}
                      >
                        ✕
                      </Button>
                    </div>
                  </div>
                  
                  {/* Step config based on type */}
                  <StepConfig step={step} onChange={(config) => updateStep(step.id, { config })} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Submit */}
      <div className="flex gap-4">
        <Button onClick={handleSubmit} disabled={isLoading || steps.length === 0}>
          {isLoading ? 'Creating...' : 'Create Workflow'}
        </Button>
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </div>
  )
}

// Step configuration component
function StepConfig({ step, onChange }: { step: Step; onChange: (config: any) => void }) {
  const updateConfig = (key: string, value: any) => {
    onChange({ ...step.config, [key]: value })
  }
  
  switch (step.type) {
    case 'http_request':
      return (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>URL</Label>
            <Input
              placeholder="https://api.example.com/webhook"
              value={step.config.url || ''}
              onChange={(e) => updateConfig('url', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Method</Label>
            <select
              value={step.config.method || 'POST'}
              onChange={(e) => updateConfig('method', e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
        </div>
      )
    
    case 'send_email':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>To</Label>
            <Input
              placeholder="recipient@example.com"
              value={step.config.to || ''}
              onChange={(e) => updateConfig('to', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Subject</Label>
            <Input
              placeholder="Email subject"
              value={step.config.subject || ''}
              onChange={(e) => updateConfig('subject', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Body</Label>
            <textarea
              placeholder="Email body"
              value={step.config.body || ''}
              onChange={(e) => updateConfig('body', e.target.value)}
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
        </div>
      )
    
    case 'delay':
      return (
        <div className="space-y-2">
          <Label>Delay (seconds)</Label>
          <Input
            type="number"
            placeholder="300"
            value={step.config.seconds || ''}
            onChange={(e) => updateConfig('seconds', parseInt(e.target.value))}
          />
        </div>
      )
    
    case 'trigger_event':
      return (
        <div className="space-y-2">
          <Label>Event Type</Label>
          <Input
            placeholder="e.g., record.created"
            value={step.config.event_type || ''}
            onChange={(e) => updateConfig('event_type', e.target.value)}
          />
        </div>
      )
    
    default:
      return (
        <p className="text-sm text-muted-foreground">
          Configuration for {step.type} will be added soon.
        </p>
      )
  }
}
