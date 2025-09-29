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
import { Settings, Save, X, AlertCircle, FileText, Workflow, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { ErrorWithData, vaultsApi, type Vault } from "@/lib/api";

interface VaultConfiguration {
  description: string;
  autoProcessing: boolean;
  allowedFileTypes: string[];
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
    description: "",
    autoProcessing: true,
    allowedFileTypes: ["pdf", "docx", "txt", "png", "jpg"],
    tags: []
  });
  const [newTag, setNewTag] = useState("");
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize config when vault changes
  useEffect(() => {
    if (vault && isOpen) {
      setConfig({
        description: vault.description || "",
        autoProcessing: vault.processing_config?.auto_process_documents || true,
        allowedFileTypes: vault.processing_config?.supported_formats || ["pdf", "docx", "pptx", "excel"],
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

  const handleSave = async () => {
    setIsSaving(true);
    
    try {

      // save the configuration using the Api
      await vaultsApi.updateVault(vault.id, {
        description: config.description,
        processing_config: {
          auto_process_documents: config.autoProcessing,
          supported_formats: config.allowedFileTypes
        },
        metadata: {
          ...vault.metadata,
          tags: config.tags
        }
      });

      onSave(config);
      setIsDirty(false);
      toast({
        title: "Configuration Saved",
        description: "Vault configuration has been updated successfully",
      });
      onClose();
    } catch (error) {
      console.error("Error saving vault configuration:", error);

      const errMessage = error instanceof ErrorWithData ? error.details || error.message : "Unknown error";
      toast({
        title: "Error Saving Configuration",
        description: "An error occurred while saving the vault configuration: " + errMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
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
              <CardTitle className="text-lg flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Basic Information
              </CardTitle>
              <CardDescription>
                Configure basic vault properties and metadata
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="vaultName">Vault Name</Label>
                <Input
                  id="vaultName"
                  value={vault?.name || ""}
                  disabled
                  className="bg-muted"
                />
                <p className="text-sm text-muted-foreground">
                  Vault name cannot be changed after creation
                </p>
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
              <CardTitle className="text-lg flex items-center">
                <Workflow className="h-5 w-5 mr-2" />
                Document Processing Settings
              </CardTitle>
              <CardDescription>
                Configure how documents are processed in this vault
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="pipelineName">Pipeline Name</Label>
                    <Input
                      id="pipelineName"
                      value={vault?.pipeline_name || ""}
                      disabled
                      className="bg-muted"
                    />
                    <p className="text-sm text-muted-foreground">
                      Pipeline name cannot be changed after creation
                    </p>
                  </div>
                </div>
                
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
                
              </div>
            </CardContent>
          </Card>

          {/* File Types */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                Allowed File Types
              </CardTitle>
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
                      <SelectItem value="pptx">PowerPoint</SelectItem>
                      <SelectItem value="excel">Excel</SelectItem>
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
            <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!isDirty || isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Configuration
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigureVaultDialog;