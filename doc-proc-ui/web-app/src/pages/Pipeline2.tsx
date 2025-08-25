
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Workflow, 
  Settings, 
  BarChart3, 
  Plus, 
  Play, 
  Pause, 
  CheckCircle,
  XCircle,
  ArrowLeft,
  Settings2
} from "lucide-react";
import PipelineWorkflowConfig from "../components/pipeline/PipelineWorkflowConfig";
import PipelineMetrics from "../components/pipeline/PipelineMetrics";
import PipelineSettings from "../components/pipeline/PipelineSettings";
import NewPipelineDialog from "../components/pipeline/NewPipelineDialog";

interface PipelineInfo {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'running' | 'failed';
  lastRun: string;
  documentsProcessed: number;
  created: string;
}

const mockPipelines: PipelineInfo[] = [
  {
    id: "1",
    name: "Legal Document Processing",
    description: "Extract entities and summarize legal contracts and agreements",
    status: "active",
    lastRun: "2 hours ago",
    documentsProcessed: 1247,
    created: "2024-01-15"
  },
  {
    id: "2", 
    name: "Financial Report Analysis",
    description: "Process financial documents and extract key metrics",
    status: "running",
    lastRun: "5 minutes ago",
    documentsProcessed: 892,
    created: "2024-02-01"
  }
];

const Pipeline2 = () => {
  const [activeTab, setActiveTab] = useState("workflow");
  const [selectedPipeline, setSelectedPipeline] = useState<PipelineInfo | null>(null);
  const [pipelines, setPipelines] = useState<PipelineInfo[]>(mockPipelines);
  const [isNewPipelineOpen, setIsNewPipelineOpen] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return CheckCircle;
      case 'running': return Play;
      case 'failed': return XCircle;
      default: return Pause;
    }
  };

  const handleCreatePipeline = (pipelineData: { name: string; description: string }) => {
    const newPipeline: PipelineInfo = {
      id: Date.now().toString(),
      name: pipelineData.name,
      description: pipelineData.description,
      status: 'inactive',
      lastRun: 'Never',
      documentsProcessed: 0,
      created: new Date().toISOString().split('T')[0]
    };
    setPipelines(prev => [...prev, newPipeline]);
  };

  if (selectedPipeline) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              onClick={() => setSelectedPipeline(null)}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Pipelines</span>
            </Button>
            <div>
              <h1 className="text-3xl font-bold">{selectedPipeline.name}</h1>
              <p className="text-muted-foreground">{selectedPipeline.description}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Configure
            </Button>
            <Button>
              <Play className="h-4 w-4 mr-2" />
              Run Pipeline
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="workflow" className="flex items-center gap-2">
              <Workflow className="h-4 w-4" />
              Workflow
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings2 className="h-4 w-4" />
              Settings
            </TabsTrigger>
            <TabsTrigger value="metrics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Metrics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="workflow" className="space-y-4">
            <PipelineWorkflowConfig />
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <PipelineSettings />
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <PipelineMetrics />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Document Processing Pipelines</h1>
          <p className="text-muted-foreground">Manage and monitor your document processing workflows</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setIsNewPipelineOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Pipeline
          </Button>
        </div>
      </div>

      <div className="grid gap-4">
        {pipelines.map((pipeline) => {
          const StatusIcon = getStatusIcon(pipeline.status);
          
          return (
            <Card 
              key={pipeline.id} 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedPipeline(pipeline)}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <Workflow className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{pipeline.name}</CardTitle>
                      <CardDescription>{pipeline.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(pipeline.status)}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {pipeline.status}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Last Run</p>
                    <p className="font-medium">{pipeline.lastRun}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Documents Processed</p>
                    <p className="font-medium">{pipeline.documentsProcessed.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Created</p>
                    <p className="font-medium">{pipeline.created}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <NewPipelineDialog
        isOpen={isNewPipelineOpen}
        onClose={() => setIsNewPipelineOpen(false)}
        onSave={handleCreatePipeline}
      />
    </div>
  );
};

export default Pipeline2;