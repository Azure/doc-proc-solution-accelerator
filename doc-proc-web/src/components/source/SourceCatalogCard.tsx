import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Database, Cloud, Globe, FileText, HardDrive } from "lucide-react";
import { SourceCatalogDefinition } from "@/lib/api";

interface SourceCatalogCardProps {
  source: SourceCatalogDefinition;
  onCreateInstance: (source: SourceCatalogDefinition) => void;
}

const SourceCatalogCard = ({ source, onCreateInstance }: SourceCatalogCardProps) => {
  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'database': return 'bg-purple-100 text-purple-800';
      case 'cloud-storage': return 'bg-blue-100 text-blue-800';
      case 'file-system': return 'bg-green-100 text-green-800';
      case 'web-crawler': return 'bg-orange-100 text-orange-800';
      case 'api': return 'bg-indigo-100 text-indigo-800';
      case 'sharepoint': return 'bg-cyan-100 text-cyan-800';
      case 'blob': return 'bg-teal-100 text-teal-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'database': return Database;
      case 'cloud-storage': return Cloud;
      case 'file-system': return HardDrive;
      case 'web-crawler': return Globe;
      case 'api': return FileText;
      case 'sharepoint': return FileText;
      case 'blob': return Cloud;
      default: return Database;
    }
  };

  const TypeIcon = getTypeIcon(source.type);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
              <TypeIcon className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-lg">{source.name}</CardTitle>
              <CardDescription className="line-clamp-2">{source.description}</CardDescription>
            </div>
          </div>
          {source.category && (
            <Badge className={getTypeColor(source.category)}>{source.category}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <p className="text-muted-foreground">Type</p>
            <p className="font-medium">{source.type}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Module</p>
            <Tooltip>
                <TooltipTrigger><p className="font-medium">{source.module_name && source.module_name.length > 30 ? source.module_name.substring(0, 30) + '...' : source.module_name}</p></TooltipTrigger>
                <TooltipContent>
                    <p>{source.module_name}</p>
                </TooltipContent>
            </Tooltip>
          </div>
          <div>
            <p className="text-muted-foreground">Class</p>
            <Tooltip>
                <TooltipTrigger><p className="font-medium">{source.class_name && source.class_name.length > 30 ? source.class_name.substring(0, 30) + '...' : source.class_name}</p></TooltipTrigger>
                <TooltipContent>
                    <p>{source.class_name}</p>
                </TooltipContent>
            </Tooltip>
          </div>
          <div>
            <p className="text-muted-foreground">Version</p>
            <p className="font-medium">{source.version || 'Latest'}</p>
          </div>
        </div>
        {source.tags && source.tags.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1">
              {source.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {source.tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{source.tags.length - 3}
                </Badge>
              )}
            </div>
          </div>
        )}
        <div className="flex justify-end">
          <Button variant="default" size="sm" onClick={() => onCreateInstance(source)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Instance
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SourceCatalogCard;