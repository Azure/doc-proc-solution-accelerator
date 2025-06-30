
import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  ArrowLeft, 
  Upload, 
  FileText, 
  Search,
  Download,
  Trash2,
  Calendar,
  FileIcon
} from "lucide-react";

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedAt: string;
  processed: boolean;
  status: 'processed' | 'processing' | 'failed';
}

const mockDocuments: Document[] = [
  {
    id: "1",
    name: "Contract_2024_001.pdf",
    type: "PDF",
    size: "2.3 MB",
    uploadedAt: "2024-01-15",
    processed: true,
    status: "processed"
  },
  {
    id: "2",
    name: "Financial_Report_Q1.docx",
    type: "Word Document",
    size: "1.8 MB",
    uploadedAt: "2024-01-14",
    processed: true,
    status: "processed"
  },
  {
    id: "3",
    name: "Research_Paper_Draft.pdf",
    type: "PDF",
    size: "892 KB",
    uploadedAt: "2024-01-13",
    processed: false,
    status: "processing"
  }
];

const mockVaults = [
  {
    id: "1",
    name: "Legal Documents",
    description: "Contract analysis and legal document storage",
    documentCount: 1247,
    size: "2.3 GB"
  },
  {
    id: "2", 
    name: "Financial Reports",
    description: "Quarterly reports and financial analysis documents",
    documentCount: 856,
    size: "1.8 GB"
  },
  {
    id: "3",
    name: "Research Papers", 
    description: "Academic publications and research materials",
    documentCount: 432,
    size: "892 MB"
  }
];

const VaultDetails = () => {
  const { vaultId } = useParams();
  const [documents, setDocuments] = useState<Document[]>(mockDocuments);
  const [uploadFiles, setUploadFiles] = useState<FileList | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const vault = mockVaults.find(v => v.id === vaultId);

  if (!vault) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-2">Vault not found</h2>
          <Link to="/vaults">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Vaults
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleUpload = () => {
    if (uploadFiles && uploadFiles.length > 0) {
      const newDocuments = Array.from(uploadFiles).map((file, index) => ({
        id: Date.now().toString() + index,
        name: file.name,
        type: file.type.includes('pdf') ? 'PDF' : 'Document',
        size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
        uploadedAt: new Date().toISOString().split('T')[0],
        processed: false,
        status: 'processing' as const
      }));
      
      setDocuments([...newDocuments, ...documents]);
      setUploadFiles(null);
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/vaults">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Vaults
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">{vault.name}</h1>
            <p className="text-muted-foreground">{vault.description}</p>
          </div>
        </div>
        
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Upload Documents
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload Documents</DialogTitle>
              <DialogDescription>
                Upload new documents to "{vault.name}"
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="file-upload">Select Files</Label>
                <Input
                  id="file-upload"
                  type="file"
                  multiple
                  onChange={(e) => setUploadFiles(e.target.files)}
                  accept=".pdf,.doc,.docx,.txt"
                />
              </div>
              <Button onClick={handleUpload} className="w-full">
                Upload Files
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Vault Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="font-medium">Total Documents:</span>
              <p className="text-2xl font-bold">{vault.documentCount.toLocaleString()}</p>
            </div>
            <div>
              <span className="font-medium">Total Size:</span>
              <p className="text-2xl font-bold">{vault.size}</p>
            </div>
            <div>
              <span className="font-medium">Processed:</span>
              <p className="text-2xl font-bold text-green-600">
                {documents.filter(d => d.status === 'processed').length}
              </p>
            </div>
            <div>
              <span className="font-medium">Processing:</span>
              <p className="text-2xl font-bold text-yellow-600">
                {documents.filter(d => d.status === 'processing').length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Documents</CardTitle>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search documents..."
                className="pl-10 w-64"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredDocuments.map((document) => (
              <div
                key={document.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50"
              >
                <div className="flex items-center space-x-3">
                  <FileIcon className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <h4 className="font-medium">{document.name}</h4>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>{document.type}</span>
                      <span>{document.size}</span>
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-4 w-4" />
                        <span>{document.uploadedAt}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <Badge className={getStatusColor(document.status)}>
                    {document.status}
                  </Badge>
                  
                  <div className="flex space-x-1">
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <FileText className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            
            {filteredDocuments.length === 0 && (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No documents found</h3>
                <p className="text-muted-foreground">
                  {searchQuery ? "Try adjusting your search terms" : "Upload some documents to get started"}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VaultDetails;