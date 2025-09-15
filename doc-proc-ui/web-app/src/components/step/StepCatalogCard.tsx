import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Settings } from "lucide-react";
import { StepCatalogDefinition } from "@/lib/api";

interface StepCatalogCardProps {
  step: StepCatalogDefinition;
  onCreateInstance: (step: StepCatalogDefinition) => void;
}

const StepCatalogCard = ({ step, onCreateInstance }: StepCatalogCardProps) => {
  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'connector': return 'bg-purple-100 text-purple-800';
      case 'extractor': return 'bg-orange-100 text-orange-800';
      case 'transformer': return 'bg-sky-100 text-sky-800';
      case 'processor': return 'bg-indigo-100 text-indigo-800';
      case 'input': return 'bg-emerald-100 text-emerald-800';
      case 'output': return 'bg-emerald-100 text-emerald-800';
      case 'ai': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow bg-">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
              <Settings className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-lg">{step.name}</CardTitle>
              <CardDescription className="line-clamp-2">{step.description}</CardDescription>
            </div>
          </div>
          {step.category && (
            <Badge className={getTypeColor(step.category)}>{step.category}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <p className="text-muted-foreground">Module</p>
            <Tooltip>
                <TooltipTrigger><p className="font-medium">{step.module_name && step.module_name.length > 30 ? step.module_name.substring(0, 30) + '...' : step.module_name}</p></TooltipTrigger>
                <TooltipContent>
                    <p>{step.module_name}</p>
                </TooltipContent>
            </Tooltip>
          </div>
          <div>
            <p className="text-muted-foreground">Class</p>
            <Tooltip>
                <TooltipTrigger><p className="font-medium">{step.class_name && step.class_name.length > 30 ? step.class_name.substring(0, 30) + '...' : step.class_name}</p></TooltipTrigger>
                <TooltipContent>
                    <p>{step.class_name}</p>
                </TooltipContent>
            </Tooltip>
          </div>
          <div>
            <p className="text-muted-foreground">Path</p>
            <Tooltip>
                <TooltipTrigger><p className="font-medium">{step.module_path && step.module_path.length > 30 ? step.module_path.substring(0, 30) + '...' : step.module_path}</p></TooltipTrigger>
                <TooltipContent>
                    <p>{step.module_path}</p>
                </TooltipContent>
            </Tooltip>
          </div>
          <div>
            <p className="text-muted-foreground">Version</p>
            <p className="font-medium">{step.version || 'Latest'}</p>
          </div>
        </div>
        {step.tags && step.tags.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1">
              {step.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {step.tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{step.tags.length - 3}
                </Badge>
              )}
            </div>
          </div>
        )}
        <div className="flex justify-end">
          <Button variant="default" size="sm" onClick={() => onCreateInstance(step)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Instance
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default StepCatalogCard;