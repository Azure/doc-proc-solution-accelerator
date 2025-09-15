
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Workflow, Save, Settings } from "lucide-react";

interface Pipeline {
  id: string;
  name: string;
  description: string;
  stepCount: number;
  status: 'active' | 'inactive';
}

const mockPipelines: Pipeline[] = [
  {
    id: "1",
    name: "Legal Document Processing",
    description: "Extract entities and summarize legal contracts",
    stepCount: 6,
    status: "active"
  },
  {
    id: "2",
    name: "Financial Report Analysis", 
    description: "Process financial documents and extract metrics",
    stepCount: 5,
    status: "active"
  },
  {
    id: "3",
    name: "Research Paper Summarization",
    description: "Summarize academic papers and extract insights",
    stepCount: 4,
    status: "inactive"
  }
];

interface VaultPipelineConfigProps {
  vaultName: string;
  selectedPipelineId?: string;
  onPipelineChange: (pipelineId: string) => void;
}

const VaultPipelineConfig = ({ 
  vaultName, 
  selectedPipelineId, 
  onPipelineChange 
}: VaultPipelineConfigProps) => {
  const [selectedPipeline, setSelectedPipeline] = useState(selectedPipelineId || "");

  const handlePipelineSelect = (pipelineId: string) => {
    setSelectedPipeline(pipelineId);
    onPipelineChange(pipelineId);
  };

  const selectedPipelineDetails = mockPipelines.find(p => p.id === selectedPipeline);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Workflow className="h-5 w-5" />
          Processing Pipeline
        </CardTitle>
        <CardDescription>
          Select which pipeline will process documents uploaded to "{vaultName}"
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="pipeline-select">Pipeline</Label>
          <Select value={selectedPipeline} onValueChange={handlePipelineSelect}>
            <SelectTrigger>
              <SelectValue placeholder="Select a processing pipeline" />
            </SelectTrigger>
            <SelectContent>
              {mockPipelines.map((pipeline) => (
                <SelectItem key={pipeline.id} value={pipeline.id}>
                  <div className="flex items-center justify-between w-full">
                    <div>
                      <div className="font-medium">{pipeline.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {pipeline.stepCount} steps
                      </div>
                    </div>
                    <Badge 
                      className={pipeline.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                      }
                    >
                      {pipeline.status}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedPipelineDetails && (
          <div className="p-3 bg-muted rounded-lg">
            <h4 className="font-medium mb-1">{selectedPipelineDetails.name}</h4>
            <p className="text-sm text-muted-foreground mb-2">
              {selectedPipelineDetails.description}
            </p>
            <div className="flex items-center justify-between">
              <span className="text-sm">
                {selectedPipelineDetails.stepCount} processing steps
              </span>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-1" />
                Configure
              </Button>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <Button>
            <Save className="h-4 w-4 mr-2" />
            Save Configuration
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default VaultPipelineConfig;