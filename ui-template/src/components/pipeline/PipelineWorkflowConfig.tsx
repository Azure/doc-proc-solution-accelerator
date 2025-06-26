
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  FileText, 
  Database, 
  Brain, 
  Search, 
  Upload,
  Settings,
  Plus,
  Save,
  Image,
  MessageSquare,
  ArrowRight
} from "lucide-react";
import StepInstanceDialog from "./StepInstanceDialog";
import WorkflowSequencer from "./WorkflowSequencer";
import { StepDefinition } from "./StepDefinition";

interface PipelineStep {
  id: string;
  name: string;
  type: 'connector' | 'extractor' | 'image-extractor' | 'ai-prompt' | 'summarizer' | 'output';
  icon: typeof FileText;
  description: string;
  order: number;
  enabled: boolean;
  config?: Record<string, any>;
}

// Mock available step definitions
const availableSteps: StepDefinition[] = [
  {
    id: "def1",
    name: "Azure Document Intelligence",
    description: "Extract text and layout from documents",
    type: "connector",
    module: "azure-document-intelligence",
    version: "1.2.0",
    defaultConfig: {},
    created: "2024-01-15T10:00:00Z",
    updated: "2024-01-20T14:30:00Z"
  },
  {
    id: "def2",
    name: "NLP Entity Extractor",
    description: "Extract entities using NLP",
    type: "extractor",
    module: "nlp-entity-extractor",
    version: "2.1.0",
    defaultConfig: {},
    created: "2024-01-10T09:00:00Z",
    updated: "2024-01-15T16:45:00Z"
  }
];

const stepTypeIcons = {
  connector: Upload,
  extractor: Search,
  'image-extractor': Image,
  'ai-prompt': MessageSquare,
  summarizer: Brain,
  output: Database
};

const PipelineWorkflowConfig = () => {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [selectedStep, setSelectedStep] = useState<PipelineStep | null>(null);
  const [isStepConfigOpen, setIsStepConfigOpen] = useState(false);
  const [isAddStepOpen, setIsAddStepOpen] = useState(false);

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

  const openStepConfig = (step: PipelineStep) => {
    setSelectedStep(step);
    setIsStepConfigOpen(true);
  };

  const handleStepSave = (config: any) => {
    if (selectedStep) {
      setSteps(prev => prev.map(step => 
        step.id === selectedStep.id 
          ? { ...step, name: config.instanceName, enabled: config.enabled, config: config.instanceConfig }
          : step
      ));
    }
    setIsStepConfigOpen(false);
    setSelectedStep(null);
  };

  const handleStepOrderChange = (newSteps: PipelineStep[]) => {
    setSteps(newSteps);
  };

  const handleStepRemove = (stepId: string) => {
    setSteps(prev => prev.filter(step => step.id !== stepId));
  };

  const handleAddStep = (stepDef: StepDefinition) => {
    const IconComponent = stepTypeIcons[stepDef.type];
    const newStep: PipelineStep = {
      id: Date.now().toString(),
      name: stepDef.name,
      type: stepDef.type,
      icon: IconComponent,
      description: stepDef.description,
      order: steps.length + 1,
      enabled: true
    };
    setSteps(prev => [...prev, newStep]);
    setIsAddStepOpen(false);
  };

  return (
    <div className="space-y-6">
      {/* Visual Workflow */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Workflow</CardTitle>
          <CardDescription>Visual representation of your document processing pipeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <div className="flex items-center space-x-4 min-w-max py-4">
              {steps
                .sort((a, b) => a.order - b.order)
                .map((step, index) => {
                  const IconComponent = step.icon;
                  return (
                    <div key={step.id} className="flex items-center">
                      <div className="flex flex-col items-center space-y-2">
                        <div className="relative group">
                          <div 
                            className={`w-12 h-12 rounded-full ${step.enabled ? 'bg-blue-500' : 'bg-gray-300'} flex items-center justify-center shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer`}
                            onClick={() => openStepConfig(step)}
                          >
                            <IconComponent className="h-5 w-5 text-white" />
                          </div>
                          
                          <div className="mt-2 text-center max-w-[80px]">
                            <h4 className="text-xs font-medium truncate">{step.name}</h4>
                            <Badge className={`${getTypeColor(step.type)} text-xs mt-1`}>
                              {step.type}
                            </Badge>
                          </div>

                          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button 
                              variant="outline" 
                              size="sm"
                              className="text-xs h-6 px-2"
                              onClick={() => openStepConfig(step)}
                            >
                              <Settings className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                      
                      {index < steps.length - 1 && (
                        <div className="flex items-center mx-3">
                          <ArrowRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  );
                })}
              
              <div className="flex items-center ml-3">
                <Dialog open={isAddStepOpen} onOpenChange={setIsAddStepOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="w-12 h-12 rounded-full flex flex-col items-center justify-center border-dashed border-2">
                      <Plus className="h-4 w-4 mb-1" />
                      <span className="text-xs">Add</span>
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Pipeline Step</DialogTitle>
                      <DialogDescription>Choose from available step definitions</DialogDescription>
                    </DialogHeader>
                    <div className="grid grid-cols-1 gap-4">
                      {availableSteps.map((stepDef) => {
                        const IconComponent = stepTypeIcons[stepDef.type];
                        return (
                          <Button
                            key={stepDef.id}
                            variant="outline"
                            className="h-16 flex items-center justify-start space-x-3 p-4"
                            onClick={() => handleAddStep(stepDef)}
                          >
                            <IconComponent className="h-6 w-6" />
                            <div className="text-left">
                              <div className="font-medium">{stepDef.name}</div>
                              <div className="text-sm text-muted-foreground">{stepDef.description}</div>
                            </div>
                          </Button>
                        );
                      })}
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Sequencer */}
      <WorkflowSequencer
        steps={steps}
        onStepOrderChange={handleStepOrderChange}
        onStepRemove={handleStepRemove}
        onStepAdd={() => setIsAddStepOpen(true)}
      />

      {/* Step Instance Configuration Dialog */}
      {selectedStep && (
        <StepInstanceDialog
          isOpen={isStepConfigOpen}
          onClose={() => {
            setIsStepConfigOpen(false);
            setSelectedStep(null);
          }}
          stepName={selectedStep.name}
          stepType={selectedStep.type}
          onSave={handleStepSave}
        />
      )}

      <div className="flex justify-end">
        <Button>
          <Save className="h-4 w-4 mr-2" />
          Save Pipeline Configuration
        </Button>
      </div>
    </div>
  );
};

export default PipelineWorkflowConfig;