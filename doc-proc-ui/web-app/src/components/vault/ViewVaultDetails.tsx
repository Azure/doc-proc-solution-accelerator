import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  Play,
  ArrowLeft,
  Workflow,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  RefreshCw,
  Settings,
  Trash2
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import UploadVaultDocuments from "@/components/vault/UploadVaultDocuments";
import ConfigureVaultDialog from "@/components/vault/ConfigureVaultDialog";
import VaultDocumentsTable from "@/components/vault/VaultDocumentsTable";
import ViewPipelineOutput from "@/components/vault/ViewPipelineOutput";
import { 
  type Vault, 
  type Pipeline,
  type DocumentInfo,
  vaultsApi,
  pipelinesApi,
  ErrorWithData
} from "@/lib/api";

interface ViewVaultDetailsProps {
  vault: Vault;
  onBack: () => void;
  onProcessAllDocuments: () => void;
  onRefreshVault: () => void;
}

const ViewVaultDetails = ({ 
  vault, 
  onBack, 
  onProcessAllDocuments,
  onRefreshVault
}: ViewVaultDetailsProps) => {
  const { toast } = useToast();

  // Pipeline state
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [pipelineCache, setPipelineCache] = useState<Map<string, Pipeline>>(new Map());

  // Dialog states
  const [isConfigureDialogOpen, setIsConfigureDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isPipelineOutputOpen, setIsPipelineOutputOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentInfo | null>(null);

  // Delete confirmation state
  const [confirmDeleteDocuments, setConfirmDeleteDocuments] = useState(false);
  const [vaultNameConfirmation, setVaultNameConfirmation] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  // Load pipeline data when component mounts or vault changes
  useEffect(() => {
    if (vault.pipeline_name) {
      loadPipeline(vault.pipeline_name);
    } else {
      setPipeline(null);
    }
  }, [vault.pipeline_name]);

  const loadPipeline = async (pipelineName: string) => {
    // Check cache first
    if (pipelineCache.has(pipelineName)) {
      setPipeline(pipelineCache.get(pipelineName) || null);
      return;
    }

    try {
      setPipelineLoading(true);
      const pipelines = await pipelinesApi.getPipelines();
      const foundPipeline = pipelines.find(p => p.name === pipelineName);
      
      // Cache the result
      if (foundPipeline) {
        const newCache = new Map(pipelineCache);
        newCache.set(pipelineName, foundPipeline);
        setPipelineCache(newCache);
        setPipeline(foundPipeline);
      } else {
        setPipeline(null);
      }
    } catch (error) {
      console.error('Error loading pipeline:', error);
      setPipeline(null);

      const errMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error';
      toast({
        title: "Error",
        description: "Failed to load pipeline information: " + errMessage,
        variant: "destructive",
      });
    } finally {
      setPipelineLoading(false);
    }
  };

  // Handler functions
  const handleUploadComplete = async (files: File[]) => {
    // request parent to refresh vault details
    onRefreshVault();
  };

  const handleProcessDocument = (documentId: string) => {
    toast({
      title: "Processing started",
      description: "Document processing has been initiated",
    });
  };

  const handleRetryProcessing = (documentId: string) => {
    // request parent to refresh vault details
    // onRefreshVault();
  };

  const handleViewProcessingPipeline = (document: DocumentInfo) => {
    setSelectedDocument(document);
    setIsPipelineOutputOpen(true);
  };

  const handleSaveVaultConfiguration = (config: any) => {
    // Here you would typically call an API to save the vault configuration
    console.log('Saving vault configuration:', config);
    toast({
      title: "Configuration Saved",
      description: "Vault configuration has been updated successfully",
    });
  };

  const handleDeleteVault = async () => {
    if (!confirmDeleteDocuments || vaultNameConfirmation !== vault.name) {
      return;
    }

    setIsDeleting(true);
    try {
      // Here you would call the delete vault API
      // await vaultsApi.deleteVault(vault.id);
      console.log('Deleting vault:', vault.id);
      await vaultsApi.deleteVault(vault.id);
      
      toast({
        title: "Vault deleted",
        description: `Vault "${vault.name}" has been deleted successfully`,
      });
      
      // Close the dialog and navigate back
      setIsDeleteDialogOpen(false);
      onBack();
    } catch (error) {
      console.error('Failed to delete vault:', error);
      const errMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error';
      toast({
        variant: "destructive",
        title: "Delete failed",
        description: `Failed to delete the vault: ${errMessage}`,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const resetDeleteDialog = () => {
    setConfirmDeleteDocuments(false);
    setVaultNameConfirmation("");
    setIsDeleteDialogOpen(false);
  };

  // Computed values
  const activeJobs = vault.stats?.active_batch_executions_count || 0;
  const completedJobs = vault.stats?.completed_batch_executions_count || 0;
  const failedJobs = vault.stats?.failed_batch_executions_count || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Vaults
          </Button>
          <div className="flex-1">
            <h2 className="text-3xl font-bold tracking-tight">{vault.name}</h2>
            <p className="text-muted-foreground">
              {vault.description || "No description available"}
            </p>
          </div>
          {vault.pipeline_name && (
            <Badge variant="outline" className="bg-blue-50">
              <Workflow className="h-3 w-3 mr-1" />
              Pipeline: {pipelineLoading ? "Loading..." : (pipeline?.name || vault.pipeline_name)}
            </Badge>
          )}
        </div>
        <div className="flex space-x-3">
          <Button 
            size="lg" 
            variant="outline" 
            onClick={() => setIsConfigureDialogOpen(true)}
          >
            <Settings className="h-5 w-5 mr-2" />
            Configure
          </Button>
          <UploadVaultDocuments 
            vault={vault}
            onUploadComplete={handleUploadComplete}
          />
          {/* <Button size="lg" variant="outline" onClick={onProcessAllDocuments}>
            <Play className="h-5 w-5 mr-2" />
            Process All Documents
          </Button> */}
          <Button 
            size="lg" 
            variant="destructive" 
            onClick={() => setIsDeleteDialogOpen(true)}
          >
            <Trash2 className="h-5 w-5 mr-2" />
            Delete Vault
          </Button>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-4">
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Total Documents</CardTitle>
            <FileText className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{vault.stats?.total_documents || 0}</div>
          </CardContent>
        </Card>
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Active Jobs</CardTitle>
            <Activity className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{activeJobs}</div>
          </CardContent>
        </Card>
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Completed Jobs</CardTitle>
            <CheckCircle className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{completedJobs}</div>
          </CardContent>
        </Card>
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Failed Jobs</CardTitle>
            <AlertCircle className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{failedJobs}</div>
          </CardContent>
        </Card>
      </div>

        
      <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Documents in {vault.name}</CardTitle>
                  <CardDescription>
                    Documents stored in this vault and their processing status.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <VaultDocumentsTable
                vault={vault}
                onViewProcessingPipeline={handleViewProcessingPipeline}
                onProcessDocument={handleProcessDocument}
                onRetryProcessing={handleRetryProcessing}
              />
            </CardContent>
          </Card>


      {/* ViewPipelineOutput Component */}
      <ViewPipelineOutput
        isOpen={isPipelineOutputOpen}
        onClose={() => setIsPipelineOutputOpen(false)}
        selectedDocument={selectedDocument}
        pipeline={pipeline}
      />

      {/* Configure Vault Dialog */}
      <ConfigureVaultDialog
        vault={vault}
        isOpen={isConfigureDialogOpen}
        onClose={() => setIsConfigureDialogOpen(false)}
        onSave={handleSaveVaultConfiguration}
      />

      {/* Delete Vault Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={(open) => !open && resetDeleteDialog()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-destructive">Delete Vault</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete the vault "{vault.name}" and all associated data.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>
                This will permanently delete the vault and cannot be undone.
              </AlertDescription>
            </Alert>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="confirm-delete-documents"
                  checked={confirmDeleteDocuments}
                  onCheckedChange={setConfirmDeleteDocuments}
                />
                <Label htmlFor="confirm-delete-documents" className="text-sm">
                  I understand that all documents in this vault will be permanently deleted
                </Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="vault-name-confirmation">
                  Type <span className="font-mono font-bold">{vault.name}</span> to confirm deletion:
                </Label>
                <Input
                  id="vault-name-confirmation"
                  placeholder="Enter vault name"
                  value={vaultNameConfirmation}
                  onChange={(e) => setVaultNameConfirmation(e.target.value)}
                  disabled={isDeleting}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={resetDeleteDialog}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteVault}
              disabled={!confirmDeleteDocuments || vaultNameConfirmation !== vault.name || isDeleting}
            >
              {isDeleting ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Vault
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ViewVaultDetails;