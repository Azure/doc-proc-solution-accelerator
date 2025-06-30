import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Database, 
  Plus, 
  Settings, 
  Upload, 
  FileText, 
  Search,
  Workflow,
  Bot,
  ExternalLink
} from "lucide-react";
import VaultPipelineConfig from "@/components/vault/VaultPipelineConfig";

interface Vault {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  size: string;
  lastUpdated: string;
  status: 'active' | 'inactive';
  searchIndexed: boolean;
  pipelineId?: string;
  autoProcess: boolean;
}

const mockVaults: Vault[] = [
  {
    id: "1",
    name: "Legal Documents",
    description: "Contract analysis and legal document storage",
    documentCount: 1247,
    size: "2.3 GB",
    lastUpdated: "2 hours ago",
    status: "active",
    searchIndexed: true,
    pipelineId: "1",
    autoProcess: true
  },
  {
    id: "2", 
    name: "Financial Reports",
    description: "Quarterly reports and financial analysis documents",
    documentCount: 856,
    size: "1.8 GB", 
    lastUpdated: "1 day ago",
    status: "active",
    searchIndexed: true,
    pipelineId: "2",
    autoProcess: false
  },
  {
    id: "3",
    name: "Research Papers", 
    description: "Academic publications and research materials",
    documentCount: 432,
    size: "892 MB",
    lastUpdated: "3 days ago", 
    status: "inactive",
    searchIndexed: false,
    autoProcess: true
  }
];

const Vaults6 = () => {
  const [vaults, setVaults] = useState<Vault[]>(mockVaults);
  const [newVaultName, setNewVaultName] = useState("");
  const [newVaultDescription, setNewVaultDescription] = useState("");
  const [configureVault, setConfigureVault] = useState<Vault | null>(null);
  const [searchIndexVault, setSearchIndexVault] = useState<Vault | null>(null);
  const [searchEndpoint, setSearchEndpoint] = useState("");
  const [searchApiKey, setSearchApiKey] = useState("");
  const [searchIndexName, setSearchIndexName] = useState("");

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleCreateVault = () => {
    if (newVaultName.trim()) {
      const newVault: Vault = {
        id: Date.now().toString(),
        name: newVaultName,
        description: newVaultDescription,
        documentCount: 0,
        size: "0 MB",
        lastUpdated: "Just now",
        status: "active",
        searchIndexed: false,
        autoProcess: false
      };
      setVaults([...vaults, newVault]);
      setNewVaultName("");
      setNewVaultDescription("");
    }
  };

  const handleConfigureVault = (vault: Vault, pipelineId: string, autoProcess: boolean) => {
    setVaults(vaults.map(v => 
      v.id === vault.id 
        ? { ...v, pipelineId, autoProcess }
        : v
    ));
    setConfigureVault(null);
  };

  const handleConfigureSearchIndex = () => {
    if (searchIndexVault) {
      setVaults(vaults.map(v => 
        v.id === searchIndexVault.id 
          ? { ...v, searchIndexed: true }
          : v
      ));
      setSearchIndexVault(null);
      setSearchEndpoint("");
      setSearchApiKey("");
      setSearchIndexName("");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Document Vaults</h1>
          <p className="text-muted-foreground">
            Manage your document collections and storage vaults
          </p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Vault
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Vault</DialogTitle>
              <DialogDescription>
                Create a new document vault to organize your files
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="vault-name">Vault Name</Label>
                <Input
                  id="vault-name"
                  value={newVaultName}
                  onChange={(e) => setNewVaultName(e.target.value)}
                  placeholder="Enter vault name"
                />
              </div>
              <div>
                <Label htmlFor="vault-description">Description</Label>
                <Textarea
                  id="vault-description"
                  value={newVaultDescription}
                  onChange={(e) => setNewVaultDescription(e.target.value)}
                  placeholder="Enter vault description"
                />
              </div>
              <Button onClick={handleCreateVault} className="w-full">
                Create Vault
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {vaults.map((vault) => (
          <Card key={vault.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Database className="h-5 w-5" />
                  <CardTitle className="text-lg">{vault.name}</CardTitle>
                </div>
                <Badge className={getStatusColor(vault.status)}>
                  {vault.status}
                </Badge>
              </div>
              <CardDescription>{vault.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Documents:</span>
                  <p className="text-muted-foreground">{vault.documentCount.toLocaleString()}</p>
                </div>
                <div>
                  <span className="font-medium">Size:</span>
                  <p className="text-muted-foreground">{vault.size}</p>
                </div>
                <div>
                  <span className="font-medium">Last Updated:</span>
                  <p className="text-muted-foreground">{vault.lastUpdated}</p>
                </div>
                <div>
                  <span className="font-medium">Search Index:</span>
                  <p className="text-muted-foreground">
                    {vault.searchIndexed ? "Indexed" : "Not indexed"}
                  </p>
                </div>
              </div>
              
              <div className="flex flex-col space-y-2">
                <Link to={`/vaults/${vault.id}`}>
                  <Button variant="default" size="sm" className="w-full">
                    <FileText className="h-4 w-4 mr-2" />
                    Browse Documents
                    <ExternalLink className="h-4 w-4 ml-2" />
                  </Button>
                </Link>
                
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload
                  </Button>
                  
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => setConfigureVault(vault)}
                      >
                        <Settings className="h-4 w-4 mr-2" />
                        Configure
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Configure Vault</DialogTitle>
                        <DialogDescription>
                          Configure processing pipeline and settings for "{vault.name}"
                        </DialogDescription>
                      </DialogHeader>
                      {configureVault && (
                        <VaultConfigureDialog
                          vault={configureVault}
                          onSave={handleConfigureVault}
                          onCancel={() => setConfigureVault(null)}
                        />
                      )}
                    </DialogContent>
                  </Dialog>
                </div>
                
                <Dialog>
                  <DialogTrigger asChild>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => setSearchIndexVault(vault)}
                    >
                      <Search className="h-4 w-4 mr-2" />
                      Configure Search Index
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Configure Azure AI Search</DialogTitle>
                      <DialogDescription>
                        Set up Azure AI Search indexing for "{vault.name}"
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="search-endpoint">Search Service Endpoint</Label>
                        <Input
                          id="search-endpoint"
                          value={searchEndpoint}
                          onChange={(e) => setSearchEndpoint(e.target.value)}
                          placeholder="https://your-service.search.windows.net"
                        />
                      </div>
                      <div>
                        <Label htmlFor="search-api-key">Admin API Key</Label>
                        <Input
                          id="search-api-key"
                          type="password"
                          value={searchApiKey}
                          onChange={(e) => setSearchApiKey(e.target.value)}
                          placeholder="Enter your Azure AI Search admin key"
                        />
                      </div>
                      <div>
                        <Label htmlFor="search-index-name">Index Name</Label>
                        <Input
                          id="search-index-name"
                          value={searchIndexName}
                          onChange={(e) => setSearchIndexName(e.target.value)}
                          placeholder="Enter index name (e.g., documents-index)"
                        />
                      </div>
                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" onClick={() => setSearchIndexVault(null)}>
                          Cancel
                        </Button>
                        <Button onClick={handleConfigureSearchIndex}>
                          Configure Search Index
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

interface VaultConfigureDialogProps {
  vault: Vault;
  onSave: (vault: Vault, pipelineId: string, autoProcess: boolean) => void;
  onCancel: () => void;
}

const VaultConfigureDialog = ({ vault, onSave, onCancel }: VaultConfigureDialogProps) => {
  const [selectedPipelineId, setSelectedPipelineId] = useState(vault.pipelineId || "");
  const [autoProcess, setAutoProcess] = useState(vault.autoProcess);

  const handleSave = () => {
    onSave(vault, selectedPipelineId, autoProcess);
  };

  return (
    <div className="space-y-6">
      <VaultPipelineConfig
        vaultName={vault.name}
        selectedPipelineId={selectedPipelineId}
        onPipelineChange={setSelectedPipelineId}
      />
      
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Processing Settings
          </CardTitle>
          <CardDescription>
            Configure how documents are processed when uploaded
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="auto-process">Automatic Processing</Label>
              <p className="text-sm text-muted-foreground">
                Process documents automatically when uploaded to this vault
              </p>
            </div>
            <Switch
              id="auto-process"
              checked={autoProcess}
              onCheckedChange={setAutoProcess}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end space-x-2">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave}>
          Save Configuration
        </Button>
      </div>
    </div>
  );
};

export default Vaults6;
