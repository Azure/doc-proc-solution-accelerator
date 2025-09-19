import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Settings, Save, X, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { type Vault } from "@/lib/api";

interface VaultConfiguration {
  name: string;
  description: string;
  autoProcessing: boolean;
  retentionDays: number;
  maxFileSize: number;
  allowedFileTypes: string[];
  processingPipeline: string;
  notificationsEnabled: boolean;
  tags: string[];
}

interface ConfigureVaultDialogProps {
  vault: Vault;
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: VaultConfiguration) => void;
}

const ConfigureVaultDialog = ({ vault, isOpen, onClose, onSave }: ConfigureVaultDialogProps) => {
  const { toast } = useToast();
  const [config, setConfig] = useState<VaultConfiguration>({
    name: "",
    description: "",
    autoProcessing: true,
    retentionDays: 365,
    maxFileSize: 100,
    allowedFileTypes: ["pdf", "docx", "txt", "png", "jpg"],
    processingPipeline: "default",
    notificationsEnabled: true,
    tags: []
  });
  const [newTag, setNewTag] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  // Initialize config when vault changes
  useEffect(() => {
    if (vault && isOpen) {
      setConfig({
        name: vault.name || "",
        description: vault.description || "",
        autoProcessing: vault.processing_config?.auto_process_documents || true,
        retentionDays: vault.metadata?.retention_days || 365,
        maxFileSize: vault.metadata?.max_file_size_mb || 100,
        allowedFileTypes: vault.processing_config?.supported_formats || ["pdf", "docx", "txt", "png", "jpg"],
        processingPipeline: vault.pipeline_name || "Not set",
        notificationsEnabled: vault.metadata?.notifications_enabled || true,
        tags: vault.metadata?.tags || []
      });
      setIsDirty(false);
    }
  }, [vault, isOpen]);

  const handleInputChange = (field: keyof VaultConfiguration, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
    setIsDirty(true);
  };

  const handleAddTag = () => {
    if (newTag.trim() && !config.tags.includes(newTag.trim())) {
      handleInputChange("tags", [...config.tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    handleInputChange("tags", config.tags.filter(tag => tag !== tagToRemove));
  };

  const handleAddFileType = (fileType: string) => {
    if (fileType && !config.allowedFileTypes.includes(fileType)) {
      handleInputChange("allowedFileTypes", [...config.allowedFileTypes, fileType]);
    }
  };

  const handleRemoveFileType = (fileType: string) => {
    if (config.allowedFileTypes.length > 1) {
      handleInputChange("allowedFileTypes", config.allowedFileTypes.filter(type => type !== fileType));
    }
  };

  const handleSave = () => {
    if (!config.name.trim()) {
      toast({
        title: "Validation Error",
        description: "Vault name is required",
        variant: "destructive",
      });
      return;
    }

    onSave(config);
    setIsDirty(false);
    toast({
      title: "Configuration Saved",
      description: "Vault configuration has been updated successfully",
    });
    onClose();
  };

  const handleCancel = () => {
    if (isDirty) {
      if (confirm("You have unsaved changes. Are you sure you want to close?")) {
        onClose();
      }
    } else {
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Configure Vault</span>
          </DialogTitle>
          <DialogDescription>
            Manage settings and configuration for "{vault?.name}"
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Information</CardTitle>
              <CardDescription>
                Configure basic vault properties and metadata
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Vault Name *</Label>
                  <Input
                    id="name"
                    value={config.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    placeholder="Enter vault name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="processingPipeline">Processing Pipeline</Label>
                  <Select 
                    value={config.processingPipeline} 
                    onValueChange={(value) => handleInputChange("processingPipeline", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select pipeline" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default Pipeline</SelectItem>
                      <SelectItem value="ocr">OCR Processing</SelectItem>
                      <SelectItem value="nlp">NLP Analysis</SelectItem>
                      <SelectItem value="custom">Custom Pipeline</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={config.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  placeholder="Enter vault description"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Processing Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Processing Settings</CardTitle>
              <CardDescription>
                Configure how documents are processed in this vault
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto Processing</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically process documents when uploaded
                  </p>
                </div>
                <Switch
                  checked={config.autoProcessing}
                  onCheckedChange={(checked) => handleInputChange("autoProcessing", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Send notifications for processing events
                  </p>
                </div>
                <Switch
                  checked={config.notificationsEnabled}
                  onCheckedChange={(checked) => handleInputChange("notificationsEnabled", checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Storage Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Storage Settings</CardTitle>
              <CardDescription>
                Configure storage limits and retention policies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="retentionDays">Retention Period (Days)</Label>
                  <Input
                    id="retentionDays"
                    type="number"
                    value={config.retentionDays}
                    onChange={(e) => handleInputChange("retentionDays", parseInt(e.target.value) || 365)}
                    min="1"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="maxFileSize">Max File Size (MB)</Label>
                  <Input
                    id="maxFileSize"
                    type="number"
                    value={config.maxFileSize}
                    onChange={(e) => handleInputChange("maxFileSize", parseInt(e.target.value) || 100)}
                    min="1"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* File Types */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Allowed File Types</CardTitle>
              <CardDescription>
                Configure which file types can be uploaded to this vault
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {config.allowedFileTypes.map((fileType) => (
                    <Badge key={fileType} variant="secondary" className="flex items-center space-x-1">
                      <span>.{fileType}</span>
                      {config.allowedFileTypes.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveFileType(fileType)}
                          className="ml-1 hover:bg-destructive/20 rounded-full p-0.5"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      )}
                    </Badge>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <Select onValueChange={handleAddFileType}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Add file type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pdf">PDF</SelectItem>
                      <SelectItem value="docx">Word Document</SelectItem>
                      <SelectItem value="txt">Text File</SelectItem>
                      <SelectItem value="rtf">Rich Text</SelectItem>
                      <SelectItem value="png">PNG Image</SelectItem>
                      <SelectItem value="jpg">JPEG Image</SelectItem>
                      <SelectItem value="jpeg">JPEG Image</SelectItem>
                      <SelectItem value="gif">GIF Image</SelectItem>
                      <SelectItem value="tiff">TIFF Image</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tags */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Tags</CardTitle>
              <CardDescription>
                Add tags to categorize and organize this vault
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {config.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="flex items-center space-x-1">
                      <span>{tag}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:bg-destructive/20 rounded-full p-0.5"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Enter tag name"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTag();
                      }
                    }}
                  />
                  <Button type="button" variant="outline" onClick={handleAddTag}>
                    Add Tag
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isDirty && (
              <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                <AlertCircle className="h-4 w-4" />
                <span>You have unsaved changes</span>
              </div>
            )}
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!isDirty}>
              <Save className="h-4 w-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigureVaultDialog;