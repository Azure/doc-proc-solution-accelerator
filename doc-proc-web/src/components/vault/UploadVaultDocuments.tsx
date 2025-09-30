import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { 
  Upload,
  FileText,
  X,
  AlertCircle
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  vaultsApi,
  type Vault, 
  type Pipeline, 
  type DocumentInfo,
  type UploadDocumentResponse,
  ErrorWithData,
} from "@/lib/api";

interface UploadVaultDocumentsProps {
  vault: Vault;
  onUploadComplete: (files: File[]) => Promise<void>;
}

interface SelectedFile {
  file: File;
  id: string;
}

const UploadVaultDocuments = ({ vault, onUploadComplete }: UploadVaultDocumentsProps) => {
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [overwrite, setOverwrite] = useState(false);
  const [fileStatus, setFileStatus] = useState<Record<string, 'pending' | 'success' | 'failed'>>({});
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({});
  
  const resetDialogState = () => {
    setSelectedFiles([]);
    setOverwrite(false);
    setFileStatus({});
    setFileErrors({});
  };

  const handleDialogClose = (open: boolean) => {
    setIsOpen(open);
    if (!open && !isUploading) {
      resetDialogState();
    }
  };
  
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles: SelectedFile[] = Array.from(files).map((file, index) => ({
        file,
        id: `${Date.now()}-${index}`
      }));
      setSelectedFiles(prev => [...prev, ...newFiles]);
      
      // Reset the input value to allow selecting the same files again
      event.target.value = '';
    }
  };

  const handleRemoveFile = (fileId: string) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast({
        title: "No files selected",
        description: "Please select at least one file to upload.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsUploading(true);
      setFileStatus({});
      setFileErrors({});

      // Upload files in a single batch (FormData) and show status per-file based on the server response
      const filesToUpload = selectedFiles.filter(sf => isValidFileType(sf.file.name));
      if (filesToUpload.length === 0) {
        toast({ title: 'No valid files', description: 'No valid files to upload', variant: 'destructive' });
        return;
      }

      // initialize statuses
      const statusInit: Record<string, 'pending' | 'success' | 'failed'> = {};
      filesToUpload.forEach(sf => { statusInit[sf.id] = 'pending'; });
      setFileStatus(statusInit);
      setFileErrors({});

      const files = filesToUpload.map(sf => sf.file);

      const results: UploadDocumentResponse[] = await vaultsApi.uploadVaultDocuments(vault.id, files, overwrite);

      // Map filenames to selected file ids (support duplicate names)
      const nameToIds: Record<string, string[]> = {};
      filesToUpload.forEach(sf => {
        nameToIds[sf.file.name] = nameToIds[sf.file.name] || [];
        nameToIds[sf.file.name].push(sf.id);
      });

      const successfulFiles: string[] = [];

      results.forEach(res => {
        const ids = nameToIds[res.filename] || [];
        if (res.document) {
          ids.forEach(id => {
            setFileStatus(prev => ({ ...prev, [id]: 'success' }));
          });
          successfulFiles.push(res.filename);
        } else {
          ids.forEach(id => {
            setFileStatus(prev => ({ ...prev, [id]: 'failed' }));
            setFileErrors(prev => ({ ...prev, [id]: res.error || 'Upload failed' }));
          });
        }
      });

      const successCount = results.filter(r => r.document).length;
      const failCount = results.length - successCount;

      if (successCount > 0) {
        toast({ title: 'Upload complete', description: `${successCount} files uploaded`, });
      }
      if (failCount > 0) {
        toast({ title: 'Upload complete', description: `${failCount} files failed`, variant: 'destructive' });
      }

      setSelectedFiles(prev => prev.filter(sf => !successfulFiles.includes(sf.file.name)));
      
      await onUploadComplete(filesToUpload.filter(sf => successfulFiles.includes(sf.file.name)).map(sf => sf.file));

      // Hide the dialog after upload if no files remain
      if (selectedFiles.length - successfulFiles.length === 0) {
        handleDialogClose(false);
      }

      toast({
        title: "Upload completed",
        description: "Documents have been uploaded successfully",
      });

    } catch (error) {
      console.error('Error uploading files:', error);

      const errMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error';
      toast({
        title: "Upload failed",
        description: "Failed to upload files. Please try again. Error: " + errMessage,
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileType = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase() || '';
    switch (extension) {
      case 'pdf':
        return 'PDF';
      case 'doc':
      case 'docx':
        return 'Word Document';
      case 'txt':
        return 'Text File';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return 'Image';
      default:
        return extension.toUpperCase() || 'Unknown';
    }
  };

  const getFileTypeColor = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase() || '';
    switch (extension) {
      case 'pdf':
        return 'bg-red-100 text-red-800';
      case 'doc':
      case 'docx':
        return 'bg-blue-100 text-blue-800';
      case 'txt':
        return 'bg-gray-100 text-gray-800';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const isValidFileType = (fileName: string): boolean => {
    const validExtensions = ['pdf', 'doc', 'docx', 'pptx', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif'];
    const extension = fileName.split('.').pop()?.toLowerCase() || '';
    return validExtensions.includes(extension);
  };

  const hasInvalidFiles = selectedFiles.some(f => !isValidFileType(f.file.name));
  const totalSize = selectedFiles.reduce((acc, f) => acc + f.file.size, 0);
  const exceedsMaxSize = totalSize > 100 * 1024 * 1024; // 100MB total limit

  return (
    <Dialog open={isOpen} onOpenChange={handleDialogClose}>
      <DialogTrigger asChild>
        <Button size="lg" className="px-8">
          <Upload className="h-5 w-5 mr-2" />
          Upload Documents
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Documents</DialogTitle>
          <DialogDescription>
            Upload files to {vault.name} vault.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6 py-4">
          {/* File Selection Section */}
          <Card>
            <CardHeader>
              <CardTitle>Select Files</CardTitle>
              <CardDescription>
                Choose documents to upload to your vault.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-4">
                  <Input
                    id="file-upload"
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.pptx,.xlsx,.txt,.jpg,.jpeg,.png,.gif"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Label
                    htmlFor="file-upload"
                    className="cursor-pointer inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90"
                  >
                    Choose Files
                  </Label>
                  <p className="mt-2 text-sm text-gray-500">
                    PDF, DOC, DOCX, TXT, and image files up to 100MB total
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Upload Options Section */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Options</CardTitle>
              <CardDescription>
                Configure how files should be handled during upload.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="overwrite-switch" className="text-base">
                    Overwrite existing files
                  </Label>
                  <div className="text-sm text-muted-foreground">
                    Replace files with the same name if they already exist in the vault
                  </div>
                </div>
                <Switch 
                  id="overwrite-switch"
                  checked={overwrite}
                  onCheckedChange={setOverwrite}
                />
              </div>
            </CardContent>
          </Card>

          {/* Selected Files Section */}
          {selectedFiles.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Selected Files ({selectedFiles.length})</span>
                  <div className="text-sm text-muted-foreground">
                    Total Size: {formatFileSize(totalSize)}
                  </div>
                </CardTitle>
                <CardDescription>
                  Review the files you've selected for upload.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {selectedFiles.map((selectedFile) => (
                    <div
                      key={selectedFile.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="h-8 w-8 text-muted-foreground" />
                        <div>
                          <h4 className="font-medium text-sm">{selectedFile.file.name}</h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge 
                              variant="secondary" 
                              className={`text-xs ${getFileTypeColor(selectedFile.file.name)}`}
                            >
                              {getFileType(selectedFile.file.name)}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatFileSize(selectedFile.file.size)}
                            </span>
                            {!isValidFileType(selectedFile.file.name) && (
                              <div className="flex items-center space-x-1 text-red-600">
                                <AlertCircle className="h-3 w-3" />
                                <span className="text-xs">Unsupported file type</span>
                              </div>
                            )}
                          </div>
                          
                          {/* Per-file status and errors (set after batch upload) */}
                          {fileStatus[selectedFile.id] && (
                            <div className="mt-2">
                              {fileStatus[selectedFile.id] === 'success' ? (
                                <Badge variant="default" className="text-xs bg-green-50 text-green-700">Uploaded</Badge>
                              ) : fileStatus[selectedFile.id] === 'failed' ? (
                                <Badge variant="destructive" className="text-xs">Failed</Badge>
                              ) : (
                                <Badge variant="secondary" className="text-xs">Pending</Badge>
                              )}
                            </div>
                          )}

                          {fileErrors[selectedFile.id] && (
                            <div className="mt-2 flex items-start space-x-2 text-red-700 text-sm">
                              <AlertCircle className="h-4 w-4 mt-0.5" />
                              <div>{fileErrors[selectedFile.id]}</div>
                            </div>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveFile(selectedFile.id)}
                        className="h-8 w-8 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
                
                {/* Warning messages */}
                {hasInvalidFiles && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-4 w-4 text-yellow-600" />
                      <span className="text-sm text-yellow-800">
                        Some files have unsupported formats and will be skipped during upload.
                      </span>
                    </div>
                  </div>
                )}
                
                {exceedsMaxSize && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-4 w-4 text-red-600" />
                      <span className="text-sm text-red-800">
                        Total file size exceeds 100MB limit. Please remove some files.
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={() => handleDialogClose(false)}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || isUploading || hasInvalidFiles || exceedsMaxSize}
          >
            {isUploading ? (
              <>
                <Upload className="h-4 w-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload Files ({selectedFiles.filter(f => isValidFileType(f.file.name)).length})
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default UploadVaultDocuments;