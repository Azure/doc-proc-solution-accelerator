
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowUp, 
  ArrowDown, 
  Trash2, 
  Plus,
  GripVertical
} from "lucide-react";

interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  order: number;
  enabled: boolean;
}

interface WorkflowSequencerProps {
  steps: WorkflowStep[];
  onStepOrderChange: (steps: WorkflowStep[]) => void;
  onStepRemove: (stepId: string) => void;
  onStepAdd: () => void;
}

const WorkflowSequencer = ({ 
  steps, 
  onStepOrderChange, 
  onStepRemove, 
  onStepAdd 
}: WorkflowSequencerProps) => {
  const moveStep = (index: number, direction: 'up' | 'down') => {
    const newSteps = [...steps];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex >= 0 && targetIndex < newSteps.length) {
      [newSteps[index], newSteps[targetIndex]] = [newSteps[targetIndex], newSteps[index]];
      
      // Update order numbers
      newSteps.forEach((step, idx) => {
        step.order = idx + 1;
      });
      
      onStepOrderChange(newSteps);
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Workflow Sequence</CardTitle>
        <CardDescription>Configure the order of pipeline steps</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {steps.map((step, index) => (
            <div 
              key={step.id} 
              className="flex items-center space-x-3 p-3 border rounded-lg bg-card"
            >
              <div className="flex items-center space-x-2">
                <GripVertical className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium w-6 text-center">{step.order}</span>
              </div>
              
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="font-medium">{step.name}</h4>
                  <Badge className={getTypeColor(step.type)}>{step.type}</Badge>
                  {!step.enabled && (
                    <Badge variant="secondary">Disabled</Badge>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => moveStep(index, 'up')}
                  disabled={index === 0}
                >
                  <ArrowUp className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => moveStep(index, 'down')}
                  disabled={index === steps.length - 1}
                >
                  <ArrowDown className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onStepRemove(step.id)}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
          
          <Button 
            variant="outline" 
            className="w-full" 
            onClick={onStepAdd}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Step
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default WorkflowSequencer;