
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  FileText, 
  Database, 
  Brain, 
  Search, 
  Upload,
  ArrowRight,
  Settings,
  Trash2
} from "lucide-react";

interface PipelineStep {
  id: string;
  name: string;
  type: 'connector' | 'extractor' | 'summarizer' | 'output';
  icon: typeof FileText;
  description: string;
  config?: Record<string, any>;
}

const PipelineWorkflow = () => {
  const [steps, setSteps] = useState<PipelineStep[]>([
    {
      id: "1",
      name: "Document Ingestion",
      type: "connector",
      icon: Upload,
      description: "Extract text from uploaded documents"
    },
    {
      id: "2", 
      name: "Entity Extraction",
      type: "extractor",
      icon: Search,
      description: "Extract key entities and information"
    },
    {
      id: "3",
      name: "AI Summarization",
      type: "summarizer", 
      icon: Brain,
      description: "Generate document summary using LLM"
    },
    {
      id: "4",
      name: "Database Storage",
      type: "output",
      icon: Database,
      description: "Store processed data in Cosmos DB"
    }
  ]);

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'connector': return 'bg-purple-100 text-purple-800';
      case 'extractor': return 'bg-orange-100 text-orange-800';
      case 'summarizer': return 'bg-cyan-100 text-cyan-800';
      case 'output': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Workflow</CardTitle>
          <CardDescription>Configure your document processing pipeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {steps.map((step, index) => {
              const IconComponent = step.icon;
              return (
                <div key={step.id} className="relative">
                  <div className="flex items-center space-x-4 p-4 border rounded-lg bg-card">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                        <IconComponent className="h-6 w-6 text-muted-foreground" />
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium">{step.name}</h3>
                        <Badge className={getTypeColor(step.type)}>{step.type}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
                    </div>
                    
                    <div className="flex-shrink-0 flex space-x-2">
                      <Button variant="ghost" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {index < steps.length - 1 && (
                    <div className="flex justify-center my-2">
                      <ArrowRight className="h-5 w-5 text-muted-foreground" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineWorkflow;