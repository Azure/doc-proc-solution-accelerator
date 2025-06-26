
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  Upload, 
  Search, 
  Brain, 
  Database, 
  Image, 
  MessageSquare,
  Settings,
  Trash2,
  Plus,
  FileText,
  Save
} from "lucide-react";

export interface StepDefinition {
  id: string;
  name: string;
  description: string;
  type: 'connector' | 'extractor' | 'image-extractor' | 'ai-prompt' | 'summarizer' | 'output';
  module: string;
  version: string;
  defaultConfig: Record<string, any>;
  created: string;
  updated: string;
}

const stepTypeIcons = {
  connector: Upload,
  extractor: Search,
  'image-extractor': Image,
  'ai-prompt': MessageSquare,
  summarizer: Brain,
  output: Database
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

interface StepDefinitionCardProps {
  step: StepDefinition;
  onEdit: (step: StepDefinition) => void;
  onDelete: (stepId: string) => void;
}

const StepDefinitionCard = ({ step, onEdit, onDelete }: StepDefinitionCardProps) => {
  const IconComponent = stepTypeIcons[step.type];

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
              <IconComponent className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-lg">{step.name}</CardTitle>
              <CardDescription>{step.description}</CardDescription>
            </div>
          </div>
          <Badge className={getTypeColor(step.type)}>{step.type}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <p className="text-muted-foreground">Module</p>
            <p className="font-medium">{step.module}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Version</p>
            <p className="font-medium">{step.version}</p>
          </div>
        </div>
        <div className="flex justify-end space-x-2">
          <Button variant="outline" size="sm" onClick={() => onEdit(step)}>
            <Settings className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="outline" size="sm" onClick={() => onDelete(step.id)} className="text-destructive">
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default StepDefinitionCard;