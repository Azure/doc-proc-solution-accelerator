import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  Plus, 
  Search, 
  FolderOpen, 
  FileText,
  Workflow,
  Database,
  Activity
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import CreateVaultDialog from "@/components/vault/CreateVaultDialog";
import ViewVaultDetails from "@/components/vault/ViewVaultDetails";
import { 
  vaultsApi, 
  type Vault, 
  type VaultCreateRequest, 
  type DocumentInfo
} from "@/lib/api";

const Vaults = () => {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedVault, setSelectedVault] = useState<string | null>(null);
  
  // Data states
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLoadingError, setIsLoadingError] = useState(false);

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const vaultsData = await vaultsApi.getVaults();
      setVaults(vaultsData);
      setIsLoadingError(false);

    } catch (error) {
      console.error('Error loading data:', error);
      
      setIsLoadingError(true);
      
      toast({
        title: "Error",
        description: "Failed to load data. Check the App Health status and ensure connectivity to backend services.",
        variant: "destructive",
      });
      
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVault = async (vaultRequest: VaultCreateRequest) => {
    try {
      const vault = await vaultsApi.createVault(vaultRequest);
      
      setVaults([...vaults, vault]);
      
      toast({
        title: "Success",
        description: `Vault "${vaultRequest.name}" created successfully`,
      });

    } catch (error) {
      console.error('Error creating vault:', error);
      toast({
        title: "Error",
        description: "Failed to create vault",
        variant: "destructive",
      });
      throw error; // Re-throw to let the dialog handle the error state
    }
  };

  const handleProcessAllDocuments = async () => {
    if (!selectedVault) return;
    
    try {
      
      toast({
        title: "Processing started",
        description: "All documents are being processed",
      });
    } catch (error) {
      console.error('Error processing vault:', error);
      toast({
        title: "Error", 
        description: "Failed to start vault processing",
        variant: "destructive",
      });
    }
  };


  const filteredVaults = vaults.filter(vault =>
    vault.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (vault.description && vault.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const currentVault = selectedVault ? vaults.find(v => v.id === selectedVault) : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading vaults...</p>
        </div>
      </div>
    );
  }
    
  if (selectedVault && currentVault) {
    return (
      <ViewVaultDetails 
        vault={currentVault}
        onBack={() => {
          setSelectedVault(null);
          loadData();
        }}
        onProcessAllDocuments={handleProcessAllDocuments}
        onRefreshVault={loadData}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Document Vaults</h2>
          <p className="text-muted-foreground">
            Create and manage your document storage vaults.
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Vault
        </Button>
      </div>

      <CreateVaultDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onCreateVault={handleCreateVault}
        loading={loading}
      />

      <div className="flex items-center space-x-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search vaults..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoadingError && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="py-4">
            <p className="text-red-700 text-center">
              Error loading vaults. Please check the App Health status and ensure connectivity to backend services.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoadingError && filteredVaults.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <FolderOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              {vaults.length === 0 ? (
                <>
                  <p className="text-muted-foreground mb-2">No vaults found.</p>
                  <p className="text-sm text-muted-foreground">Create your first vault to store and process documents.</p>
                </>
              ) : (
                <>
                  <p className="text-muted-foreground mb-2">No vaults match your search.</p>
                  <p className="text-sm text-muted-foreground">Try adjusting your search terms or create a new vault.</p>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredVaults.map((vault) => (
            <Card 
              key={vault.id} 
              className="hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedVault(vault.id)}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center space-x-2">
                  <FolderOpen className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{vault.name}</CardTitle>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge
                    variant={vault.status === "active" ? "default" : "secondary"}
                  >
                    {vault.status}
                  </Badge>
                  {vault.pipeline_name && (
                    <Badge variant="outline" className="bg-blue-50">
                      <Workflow className="h-3 w-3 mr-1" />
                      Pipeline
                    </Badge>
                  )}
                  {vault.source_instance_name && (
                    <Badge variant="outline" className="bg-blue-50">
                      <Database className="h-3 w-3 mr-1" />
                      Source
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="mb-4">
                  {vault.description || "No description available"}
                </CardDescription>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Documents:</span>
                    <div className="flex items-center space-x-1">
                      <FileText className="h-3 w-3" />
                      <span>{vault.stats.total_documents}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Created:</span>
                    <span>{new Date(vault.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Last updated:</span>
                    <span>{new Date(vault.updated_at).toLocaleDateString()}</span>
                  </div>
                  {vault.pipeline_name && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Pipeline:</span>
                      <span className="text-xs bg-blue-100 px-2 py-1 rounded">
                        {vault.pipeline_name}
                      </span>
                    </div>
                  )}
                  {vault.source_instance_name && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Source:</span>
                      <span className="text-xs bg-blue-100 px-2 py-1 rounded">
                        {vault.source_instance_name}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </>
      )}
    </div>
  );
};

export default Vaults;