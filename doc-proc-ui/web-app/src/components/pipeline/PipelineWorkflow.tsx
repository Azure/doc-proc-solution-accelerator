
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  FileText, 
  Database, 
  Brain, 
  Search, 
  Upload,
  Settings,
  Trash2,
  Plus,
  Save,
  Image,
  MessageSquare,
  ChevronUp,
  ChevronDown,
  GripVertical,
  ArrowDown,
  Cog,
  Download,
  FileSliders
} from "lucide-react";
import { stepsApi, StepInstance, ApiError } from "@/lib/api";

interface PipelineWorkflowStep {
  id: string;
  stepInstanceId: string;
  stepInstance: StepInstance;
  order: number;
  enabled: boolean;
}

interface PipelineWorkflowProps {
  pipelineId?: string;
  steps?: string[]; // Step instance names/IDs from pipeline
  executionSequence?: string[]; // Execution order
  onStepsChange?: (steps: string[], executionSequence: string[]) => void;
}

const stepTypeIcons = {
  'connector': Upload,
  'extractor': Search,
  'image-extractor': Image,
  'ai-prompt': MessageSquare,
  'summarizer': Brain,
  'output': Database,
  'document-processing': FileText
};

const PipelineWorkflow = ({ pipelineId, steps = [], executionSequence = [], onStepsChange }: PipelineWorkflowProps = {}) => {
  const [availableStepInstances, setAvailableStepInstances] = useState<StepInstance[]>([]);
  const [workflowSteps, setWorkflowSteps] = useState<PipelineWorkflowStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddStepOpen, setIsAddStepOpen] = useState(false);

  // Load available step instances from API
  useEffect(() => {
    loadStepInstances();
  }, []);

  // Initialize workflow steps based on pipeline configuration
  useEffect(() => {
    if (steps.length > 0 && availableStepInstances.length > 0) {
      initializeWorkflowSteps();
    }
  }, [steps, executionSequence, availableStepInstances]);

  const loadStepInstances = async () => {
    try {
      setLoading(true);
      setError(null);
      const instances = await stepsApi.getInstances();
      setAvailableStepInstances(instances);
    } catch (err) {
      const apiError = err as ApiError;
      console.error('Error loading step instances:', err);
      setError(apiError.message || 'Failed to load step instances');
    } finally {
      setLoading(false);
    }
  };

  const initializeWorkflowSteps = () => {
    const initialSteps: PipelineWorkflowStep[] = executionSequence.map((stepName, index) => {
      const stepInstance = availableStepInstances.find(instance => 
        instance.name === stepName || instance.id === stepName
      );
      
      if (!stepInstance) {
        console.warn(`Step instance not found: ${stepName}`);
        return null;
      }

      return {
        id: `workflow-${stepInstance.id}-${index}`,
        stepInstanceId: stepInstance.id,
        stepInstance,
        order: index + 1,
        enabled: stepInstance.enabled
      };
    }).filter(Boolean) as PipelineWorkflowStep[];

    setWorkflowSteps(initialSteps);
  };

  const getStepIcon = (stepInstance: StepInstance) => {
    const category = stepInstance.category?.toLowerCase() || '';
        
    if (category) {
      // Try to match based on category or module name
      if (category.includes('connector') || category.includes('input')) return Download;
      if (category.includes('extractor') || category.includes('transformer') || category.includes('processor')) return Cog;
      if (category.includes('image')) return Image;
      if (category.includes('ai') || category.includes('nlp')) return Brain;
      if (category.includes('output') || category.includes('storage')) return Upload;
    }
    
    return FileSliders; // Default icon
  };

  const getStepTypeFromCategory = (stepInstance: StepInstance): string => {
    const category = stepInstance.category?.toLowerCase() || '';
    
    if (category.includes('connector') || category.includes('input')) return 'connector';
    if (category.includes('extractor') || category.includes('transformer') || category.includes('processor')) return 'extractor-processor';
    if (category.includes('image')) return 'image-extractor';
    if (category.includes('ai') || category.includes('prompt')) return 'ai-prompt';
    if (category.includes('summariz') || category.includes('nlp')) return 'summarizer';
    if (category.includes('output') || category.includes('storage')) return 'output';
    
    return 'document-processing'; // Default type
  };

  const addStepToWorkflow = (stepInstance: StepInstance) => {
    const newWorkflowStep: PipelineWorkflowStep = {
      id: `workflow-${stepInstance.id}-${Date.now()}`,
      stepInstanceId: stepInstance.id,
      stepInstance,
      order: workflowSteps.length + 1,
      enabled: stepInstance.enabled
    };

    const updatedSteps = [...workflowSteps, newWorkflowStep];
    setWorkflowSteps(updatedSteps);
    
    // Notify parent component of changes
    if (onStepsChange) {
      const stepIDs = updatedSteps.map(ws => ws.stepInstance.id);
      const sequence = updatedSteps
        .sort((a, b) => a.order - b.order)
        .map(ws => ws.stepInstance.id);
      onStepsChange(stepIDs, sequence);
    }

    setIsAddStepOpen(false);
  };

  const removeStepFromWorkflow = (workflowStepId: string) => {
    const updatedSteps = workflowSteps
      .filter(ws => ws.id !== workflowStepId)
      .map((ws, index) => ({ ...ws, order: index + 1 })); // Reorder

    setWorkflowSteps(updatedSteps);

    // Notify parent component of changes
    if (onStepsChange) {
      const stepIDs = updatedSteps.map(ws => ws.stepInstance.id);
      const sequence = updatedSteps
        .sort((a, b) => a.order - b.order)
        .map(ws => ws.stepInstance.id);
      onStepsChange(stepIDs, sequence);
    }
  };

  const moveStepUp = (workflowStepId: string) => {
    const currentIndex = workflowSteps.findIndex(ws => ws.id === workflowStepId);
    if (currentIndex <= 0) return; // Can't move first item up

    const updatedSteps = [...workflowSteps];
    [updatedSteps[currentIndex], updatedSteps[currentIndex - 1]] = 
    [updatedSteps[currentIndex - 1], updatedSteps[currentIndex]];

    // Update order numbers
    const reorderedSteps = updatedSteps.map((ws, index) => ({
      ...ws,
      order: index + 1
    }));

    setWorkflowSteps(reorderedSteps);

    // Notify parent component of changes
    if (onStepsChange) {
      const stepIDs = reorderedSteps.map(ws => ws.stepInstance.id);
      const sequence = reorderedSteps.map(ws => ws.stepInstance.id);
      onStepsChange(stepIDs, sequence);
    }
  };

  const moveStepDown = (workflowStepId: string) => {
    const currentIndex = workflowSteps.findIndex(ws => ws.id === workflowStepId);
    if (currentIndex >= workflowSteps.length - 1) return; // Can't move last item down

    const updatedSteps = [...workflowSteps];
    [updatedSteps[currentIndex], updatedSteps[currentIndex + 1]] = 
    [updatedSteps[currentIndex + 1], updatedSteps[currentIndex]];

    // Update order numbers
    const reorderedSteps = updatedSteps.map((ws, index) => ({
      ...ws,
      order: index + 1
    }));

    setWorkflowSteps(reorderedSteps);

    // Notify parent component of changes
    if (onStepsChange) {
      const stepIDs = reorderedSteps.map(ws => ws.stepInstance.id);
      const sequence = reorderedSteps.map(ws => ws.stepInstance.id);
      onStepsChange(stepIDs, sequence);
    }
  };

  const handleDragStart = (e: React.DragEvent, workflowStepId: string) => {
    e.dataTransfer.setData('text/plain', workflowStepId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetWorkflowStepId: string) => {
    e.preventDefault();
    const sourceWorkflowStepId = e.dataTransfer.getData('text/plain');
    
    if (sourceWorkflowStepId === targetWorkflowStepId) return;

    const sourceIndex = workflowSteps.findIndex(ws => ws.id === sourceWorkflowStepId);
    const targetIndex = workflowSteps.findIndex(ws => ws.id === targetWorkflowStepId);

    if (sourceIndex === -1 || targetIndex === -1) return;

    const updatedSteps = [...workflowSteps];
    const [movedStep] = updatedSteps.splice(sourceIndex, 1);
    updatedSteps.splice(targetIndex, 0, movedStep);

    // Update order numbers
    const reorderedSteps = updatedSteps.map((ws, index) => ({
      ...ws,
      order: index + 1
    }));

    setWorkflowSteps(reorderedSteps);

    // Notify parent component of changes
    if (onStepsChange) {
      const stepIDs = reorderedSteps.map(ws => ws.stepInstance.id);
      const sequence = reorderedSteps.map(ws => ws.stepInstance.id);
      onStepsChange(stepIDs, sequence);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'connector': return 'bg-purple-100 text-purple-800';
      case 'extractor': return 'bg-orange-100 text-orange-800';
      case 'image-extractor': return 'bg-pink-100 text-pink-800';
      case 'ai-prompt': return 'bg-indigo-100 text-indigo-800';
      case 'summarizer': return 'bg-cyan-100 text-cyan-800';
      case 'output': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">Loading step instances...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-red-600">Error: {error}</p>
          <div className="text-center mt-4">
            <Button onClick={loadStepInstances} variant="outline">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Pipeline Workflow</CardTitle>
              <CardDescription>Configure your document processing pipeline from step instances</CardDescription>
            </div>
            <Dialog open={isAddStepOpen} onOpenChange={setIsAddStepOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Step
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Add Step to Pipeline</DialogTitle>
                  <DialogDescription>
                    Choose from available step instances to add to your pipeline workflow
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 max-h-96 overflow-y-auto">
                  {availableStepInstances
                    .filter(instance => !workflowSteps.some(ws => ws.stepInstanceId === instance.id))
                    .map((instance) => {
                      const IconComponent = getStepIcon(instance);
                      const stepType = getStepTypeFromCategory(instance);
                      return (
                        <Card 
                          key={instance.id} 
                          className="cursor-pointer hover:shadow-md transition-shadow"
                          onClick={() => addStepToWorkflow(instance)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center space-x-3">
                              <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                                <IconComponent className="h-5 w-5 text-muted-foreground" />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <h4 className="font-medium">{instance.name}</h4>
                                  <Badge className={getTypeColor(stepType)}>{stepType}</Badge>
                                  {!instance.enabled && (
                                    <Badge variant="secondary">Disabled</Badge>
                                  )}
                                </div>
                                <p className="text-sm text-muted-foreground">{instance.description}</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  {availableStepInstances.filter(instance => !workflowSteps.some(ws => ws.stepInstanceId === instance.id)).length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      All available step instances are already added to the workflow.
                    </p>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {workflowSteps.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">No steps configured yet</p>
              <Button onClick={() => setIsAddStepOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add First Step
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {workflowSteps
                .sort((a, b) => a.order - b.order)
                .map((workflowStep, index) => {
                  const { stepInstance } = workflowStep;
                  const IconComponent = getStepIcon(stepInstance);
                  const stepType = getStepTypeFromCategory(stepInstance);
                  
                  return (
                    <div key={workflowStep.id} className="relative">
                      <div 
                        className="flex items-center space-x-4 p-4 border rounded-lg bg-card cursor-move"
                        draggable
                        onDragStart={(e) => handleDragStart(e, workflowStep.id)}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, workflowStep.id)}
                      >
                        <div className="flex-shrink-0">
                          <div className="cursor-grab active:cursor-grabbing">
                            <GripVertical className="h-4 w-4 text-muted-foreground mr-2" />
                          </div>
                        </div>
                        
                        <div className="flex-shrink-0">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                            workflowStep.enabled ? 'bg-blue-500' : 'bg-gray-300'
                          }`}>
                            <IconComponent className="h-6 w-6 text-white" />
                          </div>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-lg font-medium">{stepInstance.name}</h3>
                            {/* <Badge className={getTypeColor(stepType)}>{stepType}</Badge> */}
                            <Badge className={getTypeColor(stepType)}>{stepInstance.category}</Badge>
                            {!workflowStep.enabled && (
                              <Badge variant="secondary">Disabled</Badge>
                            )}
                            <span className="text-sm text-muted-foreground">#{workflowStep.order}</span>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{stepInstance.description}</p>
                        </div>
                        
                        <div className="flex-shrink-0 flex space-x-2">
                          <div className="flex flex-col gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => moveStepUp(workflowStep.id)}
                              disabled={index === 0}
                              className="h-6 w-6 p-0"
                              title="Move up"
                            >
                              <ChevronUp className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => moveStepDown(workflowStep.id)}
                              disabled={index === workflowSteps.length - 1}
                              className="h-6 w-6 p-0"
                              title="Move down"
                            >
                              <ChevronDown className="h-3 w-3" />
                            </Button>
                          </div>
                          
                         
                          <div className="flex items-center space-x-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-destructive"
                            onClick={() => removeStepFromWorkflow(workflowStep.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                          </div>

                        </div>
                      </div>
                      
                      {index < workflowSteps.length - 1 && (
                        <div className="flex justify-center my-2">
                          <ArrowDown className="h-5 w-5 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineWorkflow;