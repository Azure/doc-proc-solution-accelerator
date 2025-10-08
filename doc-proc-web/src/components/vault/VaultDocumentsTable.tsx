import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { 
  Play,
  RotateCcw,
  X,
  Workflow,
  AlertCircle,
  Clock,
  FileText,
  RefreshCw,
  ArrowUpDown,
  ChevronUp,
  ChevronDown,
  Filter,
  Search,
  Loader2,
  Info
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  vaultsApi,
  documentStatusApi,
  type Vault, 
  type DocumentInfo,
  type PaginatedResponse,
  type DocumentExecutionStatus,
  ErrorWithData
} from "@/lib/api";

interface VaultDocumentsTableProps {
  vault: Vault;
  onViewProcessingPipeline: (document: DocumentInfo) => void;
  onProcessDocument: (documentId: string) => void;
  onRetryProcessing: (documentId: string) => void;
}

const VaultDocumentsTable = ({ 
  vault, 
  onViewProcessingPipeline,
  onProcessDocument,
  onRetryProcessing
}: VaultDocumentsTableProps) => {
  const { toast } = useToast();

  // Document data and pagination
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

  // Document status tracking
  const [documentStatuses, setDocumentStatuses] = useState<Record<string, string>>({});
  const [documentStatusDetails, setDocumentStatusDetails] = useState<Record<string, DocumentExecutionStatus>>({});
  const [loadingStatuses, setLoadingStatuses] = useState<Set<string>>(new Set());
  const [batchLoadingStatus, setBatchLoadingStatus] = useState(false);
  const [statusRefreshInterval, setStatusRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const [lastStatusRefresh, setLastStatusRefresh] = useState<Date | null>(null);

  // Pagination and filtering state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [timeFilter, setTimeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortColumn, setSortColumn] = useState<keyof DocumentInfo | "">("");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Load documents when vault changes or pagination/filters change
  useEffect(() => {
    if (vault?.id) {
      loadVaultDocuments();
    }
  }, [vault.id, currentPage, pageSize, timeFilter, searchQuery, sortColumn, sortDirection]);

  // Set up auto-refresh for document statuses every 30 seconds
  useEffect(() => {
    if (documents.length > 0) {
      const interval = setInterval(() => {
        refreshVisibleDocumentStatuses();
      }, 30000); // Refresh every 30 seconds

      setStatusRefreshInterval(interval);

      return () => {
        if (interval) clearInterval(interval);
      };
    }

    return () => {
      if (statusRefreshInterval) {
        clearInterval(statusRefreshInterval);
        setStatusRefreshInterval(null);
      }
    };
  }, [documents]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (statusRefreshInterval) {
        clearInterval(statusRefreshInterval);
      }
    };
  }, []);

  // Server-side paginated API call for documents
  const loadVaultDocuments = async () => {
    try {
      setIsLoadingDocuments(true);
      
      // Build filter parameters - all filtering now handled server-side
      const params = {
        page: currentPage,
        pageSize: pageSize,
        timeFilter: timeFilter !== "all" ? timeFilter : undefined,
        search: searchQuery.trim() || undefined,
        sortBy: sortColumn || undefined,
        sortDirection: sortColumn ? sortDirection : undefined,
      };

      // Call API with server-side filtering and pagination
      const response: PaginatedResponse<DocumentInfo> = await vaultsApi.getVaultDocumentsPaginated(
        vault.id, 
        params.page, 
        params.pageSize, 
        params.timeFilter, 
        params.search, 
        params.sortBy, 
        params.sortDirection
      );

      // Server returns pre-filtered, sorted, and paginated results
      setDocuments(response.items);
      setTotalDocuments(response.total);
      
      // Fetch statuses for the loaded documents
      if (response.items.length > 0) {
        fetchDocumentStatuses(response.items);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      toast({
        title: "Error",
        description: "Failed to load vault documents",
        variant: "destructive",
      });
    } finally {
      setIsLoadingDocuments(false);
    }
  };

  const handleRetryProcessing = async (documentId: string) => {
    
    try {
      // Reset the document status to indicate it's being retried
      setDocumentStatuses(prev => ({
        ...prev,
        [documentId]: 'queued'
      }));

      // Clear any detailed status information for this document
      setDocumentStatusDetails(prev => {
        const updated = { ...prev };
        delete updated[documentId];
        return updated;
      });

      await vaultsApi.processVault(vault.id, [documentId]);

      onRetryProcessing(documentId);

      toast({
        title: "Retrying processing", 
        description: "Document processing has been requested. Results will update shortly.",
      });

      // Refresh the status for this document after a brief delay
      setTimeout(() => {
        fetchDocumentStatuses(documentId, { forceSingle: true });
      }, 1000);

    } catch (error) {
      console.error('Error retrying document processing:', error);
      
      const errorMsg = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      toast({
        title: "Error",
        description: "Failed to retry document processing: " + errorMsg,
        variant: "destructive",
      });
    }
  };

  // Real API function to fetch document statuses - handles both single and batch operations
  const fetchDocumentStatusesApi = async (
    documentIds: string | string[], 
    documentsMap?: Map<string, DocumentInfo>
  ): Promise<string | Record<string, string>> => {
    const isBatch = Array.isArray(documentIds);
    const ids = isBatch ? documentIds : [documentIds];
    
    try {
      console.log('Fetching document statuses from backend API for IDs:', ids);
      
      // Call the backend API
      const statusResults: DocumentExecutionStatus[] = await documentStatusApi.getDocumentStatus(ids);
      console.log('Backend API response:', statusResults);
      
      if (isBatch) {
        // Return Record<string, string> for batch operations
        const batchResults: Record<string, string> = {};
        const batchDetails: Record<string, DocumentExecutionStatus> = {};
        
        statusResults.forEach(status => {
          // Map batch_status to a simplified status string
          const simplifiedStatus = mapExecutionStatusToDisplayStatus(status);
          batchResults[status.document_id] = simplifiedStatus;
          batchDetails[status.document_id] = status;
        });
        
        // Store detailed status information
        setDocumentStatusDetails(prev => ({
          ...prev,
          ...batchDetails
        }));
        
        // For documents not found in results, use document's own status or fallback to current status
        ids.forEach(id => {
          if (!batchResults[id]) {
            // Try to get the document's own status from the documentsMap
            const document = documentsMap?.get(id);
            const fallbackStatus = document?.status || documentStatuses[id] || 'pending';
            batchResults[id] = fallbackStatus;
            console.log(`No processing status found for document ${id}, using document status: ${fallbackStatus}`);
          }
        });
        
        return batchResults;
      } else {
        // Return single status string for individual operations
        const statusResult = statusResults.find(s => s.document_id === ids[0]);
        if (statusResult) {
          // Store detailed status information
          setDocumentStatusDetails(prev => ({
            ...prev,
            [statusResult.document_id]: statusResult
          }));
          return mapExecutionStatusToDisplayStatus(statusResult);
        } else {
          // Document not found in execution results, use document's own status or fallback
          const document = documentsMap?.get(ids[0]);
          const fallbackStatus = document?.status || documentStatuses[ids[0]] || 'pending';
          console.log(`No processing status found for document ${ids[0]}, using document status: ${fallbackStatus}`);
          return fallbackStatus;
        }
      }
    } catch (error) {
      console.error('Error fetching document status from backend:', error);
      
      // Show user-friendly error message
      const errorMsg = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      toast({
        title: "Status Fetch Failed",
        description: `Unable to get current document status: ${errorMsg}`,
        variant: "destructive",
      });
      
      throw error;
    }
  };

  // Helper function to map DocumentExecutionStatus to display status
  const mapExecutionStatusToDisplayStatus = (status: DocumentExecutionStatus): string => {
    // First priority: Check document-specific status if available
    if (status.document && status.document.status) {
      const docStatus = status.document.status.toLowerCase();
      
      // Map document statuses to display statuses
      switch (docStatus) {
        case 'completed':
        case 'success':
        case 'successful':
        case 'succeeded':
          return 'completed';
        case 'failed':
        case 'error':
        case 'failure':
          return 'failed';
        case 'pending':
        case 'queued':
        case 'waiting':
        default:
          // If document status is not final, continue to batch status check
          break;
      }
    }
    
    // Second priority: Check batch_status if document status is not final or not available
    if (status.batch_status) {
      const batchStatus = status.batch_status.toLowerCase();
      
      // Map common batch statuses to display statuses
      switch (batchStatus) {
        case 'completed':
        case 'success':
        case 'successful':
        case 'succeeded':
          return 'completed';
        case 'failed':
        case 'error':
        case 'failure':
          return 'failed';
        case 'running':
        case 'in_progress':
        case 'processing':
          return 'processing';
        case 'pending':
        case 'queued':
        case 'submitted':
        case 'waiting':
          return 'pending';
        case 'cancelled':
        case 'canceled':
          return 'cancelled';
        default:
          return batchStatus;
      }
    }
    
    // Fallback logic based on timestamps if neither document nor batch status available
    if (status.batch_completed_at) {
      return 'completed';
    } else if (status.batch_started_at) {
      return 'processing';
    } else if (status.batch_submitted_at) {
      return 'pending';
    }
    
    // Default fallback
    return 'unknown';
  };

  // Helper function to check if a status is "final" (shouldn't be refreshed)
  const isStatusFinal = (status: string): boolean => {
    if (!status) return false;
    const finalStatuses = ['completed', 'failed', 'cancelled', 'error'];
    return finalStatuses.includes(status.toLowerCase());
  };

  // Helper function to get user-friendly status messages
  const getStatusMessage = (status: DocumentExecutionStatus): string => {
    if (status.batch_status) {
      const batchStatus = status.batch_status.toLowerCase();
      
      switch (batchStatus) {
        case 'completed':
        case 'success':
          return status.batch_completed_at 
            ? `Processing completed on ${new Date(status.batch_completed_at).toLocaleString()}`
            : 'Processing completed successfully';
        case 'failed':
        case 'error':
          return 'Processing failed - check error logs for details';
        case 'processing':
        case 'running':
          return status.batch_started_at 
            ? `Processing started ${new Date(status.batch_started_at).toLocaleString()}`
            : 'Document is currently being processed';
        case 'pending':
        case 'queued':
          return status.batch_submitted_at 
            ? `Queued for processing since ${new Date(status.batch_submitted_at).toLocaleString()}`
            : 'Document is queued for processing';
        case 'cancelled':
          return 'Processing was cancelled';
        default:
          return `Status: ${status.batch_status}`;
      }
    }
    
    return 'Status information not available';
  };

 // Consolidated function to fetch document statuses with flexible parameters
 const fetchDocumentStatuses = async (
    input: DocumentInfo[] | DocumentInfo | string[] | string,
    options: {
      forceBatch?: boolean;
      forceSingle?: boolean;
      skipLoadingState?: boolean;
      skipFinalStatuses?: boolean; // Skip documents with final statuses
    } = {}
  ) => {
    // Normalize input to document IDs and create documents map
    let documentIds: string[];
    let documentsMap: Map<string, DocumentInfo> | undefined;

    if (typeof input === 'string') {
      documentIds = [input];
      // Try to find the document in the current documents array
      const document = documents.find(doc => doc.id === input);
      if (document) {
        documentsMap = new Map([[input, document]]);
      }
    } else if (Array.isArray(input)) {
      if (typeof input[0] === 'string') {
        documentIds = input as string[];
        // Try to find documents in the current documents array
        const foundDocuments = documents.filter(doc => documentIds.includes(doc.id));
        if (foundDocuments.length > 0) {
          documentsMap = new Map(foundDocuments.map(doc => [doc.id, doc]));
        }
      } else {
        const docs = input as DocumentInfo[];
        documentIds = docs.map(doc => doc.id);
        documentsMap = new Map(docs.map(doc => [doc.id, doc]));
      }
    } else {
      const doc = input as DocumentInfo;
      documentIds = [doc.id];
      documentsMap = new Map([[doc.id, doc]]);
    }
    
    if (documentIds.length === 0) return;
    
    // Filter out documents with final statuses if requested
    if (options.skipFinalStatuses) {
      const originalCount = documentIds.length;
      documentIds = documentIds.filter(id => {
        const currentStatus = getCurrentDocumentStatus({ id } as DocumentInfo);
        return !isStatusFinal(currentStatus);
      });
      
      if (documentIds.length === 0) {
        console.log(`All ${originalCount} documents have final statuses, skipping refresh`);
        return;
      }
      
      if (documentIds.length < originalCount) {
        console.log(`Skipping refresh for ${originalCount - documentIds.length} documents with final statuses`);
      }
    }
    
    const isSingleDocument = documentIds.length === 1;
    const shouldUseBatch = options.forceBatch || (!options.forceSingle && !isSingleDocument);
    
    // Set appropriate loading states
    if (!options.skipLoadingState) {
      if (shouldUseBatch) {
        setBatchLoadingStatus(true);
      } else {
        // Prevent duplicate single document calls
        if (loadingStatuses.has(documentIds[0])) return;
        setLoadingStatuses(prev => new Set(prev).add(documentIds[0]));
      }
    }
    
    try {
      if (shouldUseBatch) {
        console.log(`Fetching batch status for ${documentIds.length} documents`);
        
        const docStatuses = await fetchDocumentStatusesApi(documentIds, documentsMap) as Record<string, string>;
        console.log('Batch status results:', docStatuses);
        
        // Update all document statuses at once
        setDocumentStatuses(prev => ({
          ...prev,
          ...docStatuses
        }));
        
      } else {
        console.log(`Fetching single status for document ${documentIds[0]}`);
        
        const status = await fetchDocumentStatusesApi(documentIds[0], documentsMap) as string;
        console.log(`Single status result: ${status}`);
        
        // Update single document status
        setDocumentStatuses(prev => ({
          ...prev,
          [documentIds[0]]: status
        }));
      }
    } catch (error) {
      console.error('Error fetching document statuses:', error);
      
      if (shouldUseBatch) {
        toast({
          title: "Batch Status Update Failed",
          description: "Could not fetch status for multiple documents. Trying individual updates...",
          variant: "destructive",
        });
        
        // Fallback to individual fetches if batch fails
        const promises = documentIds.map(id => 
          fetchDocumentStatuses(id, { forceSingle: true, skipLoadingState: true })
        );
        const results = await Promise.allSettled(promises);
        
        const successCount = results.filter(r => r.status === 'fulfilled').length;
        const failCount = results.filter(r => r.status === 'rejected').length;
        
      } else {
        toast({
          title: "Status Update Failed",
          description: `Could not fetch status for document ID: ${documentIds[0]}`,
          variant: "destructive",
        });
      }
    } finally {
      // Clear loading states
      if (!options.skipLoadingState) {
        if (shouldUseBatch) {
          setBatchLoadingStatus(false);
        } else {
          setLoadingStatuses(prev => {
            const newSet = new Set(prev);
            newSet.delete(documentIds[0]);
            return newSet;
          });
        }
      }
    }
    
    setLastStatusRefresh(new Date());
  };

  // Refresh statuses for visible documents only
  const refreshVisibleDocumentStatuses = async () => {
    if (documents.length === 0) return;
    
    console.log(`Refreshing status for ${documents.length} visible documents`);
    
    // Use the consolidated function with automatic batch/single selection
    // Skip documents that have already completed or failed
    await fetchDocumentStatuses(documents, { skipFinalStatuses: true });
  };

  // Time filter options
  const timeFilterOptions = [
    { value: "all", label: "All Time" },
    { value: "1h", label: "Last 1 Hour" },
    { value: "4h", label: "Last 4 Hours" },
    { value: "24h", label: "Last 24 Hours" },
    { value: "7d", label: "Last 7 Days" },
    { value: "30d", label: "Last 30 Days" },
  ];

  // Calculate total pages
  const totalPages = Math.ceil(totalDocuments / pageSize);

  // Handle sorting
  const handleSort = (column: keyof DocumentInfo) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle page size change
  const handlePageSizeChange = (size: string) => {
    setPageSize(parseInt(size));
    setCurrentPage(1); // Reset to first page when changing page size
  };

  // Handle time filter change
  const handleTimeFilterChange = (filter: string) => {
    setTimeFilter(filter);
    setCurrentPage(1); // Reset to first page when changing filter
  };

  // Handle search change
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1); // Reset to first page when searching
  };

  // Handle clear search
  const handleClearSearch = () => {
    setSearchQuery("");
    setCurrentPage(1);
  };

  // Render sort icon
  const renderSortIcon = (column: keyof DocumentInfo) => {
    if (sortColumn !== column) {
      return <ArrowUpDown className="ml-2 h-4 w-4" />;
    }
    return sortDirection === "asc" 
      ? <ChevronUp className="ml-2 h-4 w-4" />
      : <ChevronDown className="ml-2 h-4 w-4" />;
  };

  // Get current document status (from API or fallback to original)
  const getCurrentDocumentStatus = (doc: DocumentInfo) => {
    return documentStatuses[doc.id] || doc.status; // === 'queued' ? doc.status : 'loading';
  };

  // Get status variant for badge
  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed":
      case "processed":
        return "default";
      case "processing":
      case "queued":
        return "secondary";
      case "failed":
      case "error":
        return "destructive";
      default:
        return "secondary";
    }
  };

  // Get detailed tooltip text for status
  const getStatusTooltip = (status: string): string => {
    switch (status.toLowerCase()) {
      case "completed":
        return "Document processing completed successfully";
      case "processing":
        return "Document is currently being processed";
      case "failed":
        return "Document processing failed - check error logs";
      case "pending":
        return "Document is queued and waiting to be processed";
      case "queued":
        return "Document is in the processing queue";
      case "error":
        return "An error occurred during processing";
      case "cancelled":
        return "Document processing was cancelled";
      case "unknown":
        return "Status could not be determined";
      default:
        return `Current status: ${status}`;
    }
  };

  // Handle manual status refresh for a document
  const handleRefreshDocumentStatus = async (documentId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click if any
    await fetchDocumentStatuses(documentId, { forceSingle: true });
  };

  // Get detailed status information for a document
  const getDocumentStatusDetails = (documentId: string): DocumentExecutionStatus | null => {
    return documentStatusDetails[documentId] || null;
  };

  // Format date for display
  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'Not available';
    return new Date(dateString).toLocaleString();
  };

  // Format file size for display
  const formatFileSize = (sizeBytes: number): string => {
    const sizeMB = sizeBytes / (1024 * 1024);
    if (sizeMB < 0.01) {
      // Show in KB if less than 0.01 MB
      const sizeKB = sizeBytes / 1024;
      return `${sizeKB.toFixed(1)} KB`;
    }
    return `${sizeMB.toFixed(2)} MB`;
  };

  // Render status details dialog
  const renderStatusDetailsDialog = (doc: DocumentInfo) => {
    const statusDetail = getDocumentStatusDetails(doc.id);
    const currentStatus = getCurrentDocumentStatus(doc);

    return (
      <Dialog>
        <DialogTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-5 w-5 p-0 hover:bg-muted"
          >
            <Info className="h-3 w-3" />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Document Processing Details</DialogTitle>
            <DialogDescription>
              Detailed processing information for "{doc.name}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium">Current Status</Label>
                <div className="mt-1">
                  <Badge variant={getStatusVariant(currentStatus)}>
                    {currentStatus}
                  </Badge>
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium">Document ID</Label>
                <p className="mt-1 text-sm font-mono">{doc.id}</p>
              </div>
            </div>

            {statusDetail ? (
              <>
                {/* Processing Timeline */}
                <div>
                  <Label className="text-sm font-medium">Processing Timeline</Label>
                  <div className="mt-2 space-y-2">
                    <div className="flex justify-between items-center p-2 bg-muted/50 rounded">
                      <span className="text-sm">Submitted:</span>
                      <span className="text-sm font-mono">{formatDate(statusDetail.batch_submitted_at)}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-muted/50 rounded">
                      <span className="text-sm">Started:</span>
                      <span className="text-sm font-mono">{formatDate(statusDetail.batch_started_at)}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-muted/50 rounded">
                      <span className="text-sm">Completed:</span>
                      <span className="text-sm font-mono">{formatDate(statusDetail.batch_completed_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Batch Information */}
                <div>
                    <Label className="text-sm font-medium">Batch ID</Label>
                    <p className="mt-1 text-sm font-mono">{statusDetail.batch_id || 'Not available'}</p>
                </div>

                <div>
                    <Label className="text-sm font-medium">Pipeline Name</Label>
                    <p className="mt-1 text-sm">{statusDetail.pipeline_name || 'Not available'}</p>
                </div>

                {statusDetail.pipeline_execution_id && (
                  <div>
                    <Label className="text-sm font-medium">Pipeline Execution ID</Label>
                    <p className="mt-1 text-sm font-mono">{statusDetail.pipeline_execution_id}</p>
                  </div>
                )}

                {/* Metadata */}
                {statusDetail.batch_metadata && Object.keys(statusDetail.batch_metadata).length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Processing Metadata</Label>
                    <div className="mt-2 p-3 bg-muted/50 rounded">
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(statusDetail.batch_metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Errors */}
                {statusDetail.batch_errors && statusDetail.batch_errors.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Batch Errors</Label>
                    <div className="mt-2 p-3 bg-muted/50 rounded">
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(statusDetail.batch_errors, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Document Info from status */}
                {statusDetail.document && (
                  <div>
                    <Label className="text-sm font-medium">Document Information</Label>
                    <div className="mt-2 p-3 bg-muted/50 rounded">
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(statusDetail.document, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <>
                {/* Check if document has error information in metadata */}
                {doc.metadata?.error || doc.metadata?.error_details ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-destructive">
                      <AlertCircle className="h-5 w-5" />
                      <span className="font-medium">Document Processing Error</span>
                    </div>
                    
                    {doc.metadata.error && (
                      <div>
                        <Label className="text-sm font-medium">Error Message</Label>
                        <div className="mt-2 p-3 bg-destructive/10 border border-destructive/20 rounded">
                          <p className="text-sm text-destructive font-medium">
                            {doc.metadata.error}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {doc.metadata.error_details && (
                      <div>
                        <Label className="text-sm font-medium">Error Details</Label>
                        <div className="mt-2 p-3 bg-destructive/10 border border-destructive/20 rounded">
                          {typeof doc.metadata.error_details === 'string' ? (
                            <p className="text-sm text-destructive whitespace-pre-wrap">
                              {doc.metadata.error_details}
                            </p>
                          ) : (
                            <pre className="text-xs text-destructive overflow-auto whitespace-pre-wrap">
                              {JSON.stringify(doc.metadata.error_details, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Show document metadata if it has other useful information */}
                    {Object.keys(doc.metadata).some(key => !['error', 'error_details'].includes(key)) && (
                      <div>
                        <Label className="text-sm font-medium">Additional Metadata</Label>
                        <div className="mt-2 p-3 bg-muted/50 rounded">
                          <pre className="text-xs overflow-auto">
                            {JSON.stringify(
                              Object.fromEntries(
                                Object.entries(doc.metadata).filter(([key]) => !['error', 'error_details'].includes(key))
                              ), 
                              null, 
                              2
                            )}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No detailed processing information available for this document.</p>
                    <p className="text-sm">The document may not have been processed yet.</p>
                  </div>
                )}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <TooltipProvider>
      <div className="space-y-4">
      {/* Filters and Controls */}
      <div className="flex flex-col space-y-4 mb-6">
        {/* Search and Time Filter Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-8 w-64"
              />
              {searchQuery && (
                <X
                  className="absolute right-2 top-2.5 h-4 w-4 cursor-pointer text-muted-foreground hover:text-foreground"
                  onClick={handleClearSearch}
                />
              )}
            </div>
            
            {/* Time Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Label htmlFor="timeFilter">Filter by Submission Time:</Label>
              <Select value={timeFilter} onValueChange={handleTimeFilterChange}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Select time range" />
                </SelectTrigger>
                <SelectContent>
                  {timeFilterOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Page Size Control */}
          <div className="flex items-center space-x-2">
            <Label htmlFor="pageSize">Show:</Label>
            <Select value={pageSize.toString()} onValueChange={handlePageSizeChange}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5</SelectItem>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="25">25</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-muted-foreground">per page</span>
          </div>

          {/* Refresh Controls */}
          <div className="flex items-center space-x-2">
            {/* Refresh Documents Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={loadVaultDocuments}
                  disabled={isLoadingDocuments}
                  className="p-2"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoadingDocuments ? 'animate-spin' : ''}`} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Refresh document list</p>
              </TooltipContent>
            </Tooltip>

            {/* Batch Status Refresh Control */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={refreshVisibleDocumentStatuses}
                  disabled={batchLoadingStatus || isLoadingDocuments || documents.length === 0}
                  className="flex items-center space-x-1"
                >
                  <RefreshCw className={`h-3 w-3 ${batchLoadingStatus ? 'animate-spin' : ''}`} />
                  <span>Refresh All Status</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Refresh status for all visible documents</p>
                <p className="text-xs opacity-70">
                  Skips documents that are already completed or failed
                </p>
              </TooltipContent>
            </Tooltip>
            {batchLoadingStatus && (
              <span className="text-xs text-muted-foreground">
                Updating {documents.length} document{documents.length !== 1 ? 's' : ''}...
              </span>
            )}
          </div>
        </div>
        
        {/* Active Filters Display */}
        {(timeFilter !== "all" || searchQuery.trim()) && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Active filters:</span>
            {searchQuery.trim() && (
              <Badge variant="secondary" className="flex items-center gap-1">
                <Search className="h-3 w-3" />
                "{searchQuery}"
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={handleClearSearch}
                />
              </Badge>
            )}
            {timeFilter !== "all" && (
              <Badge variant="secondary" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {timeFilterOptions.find(opt => opt.value === timeFilter)?.label}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => handleTimeFilterChange("all")}
                />
              </Badge>
            )}
            {(timeFilter !== "all" || searchQuery.trim()) && (
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  handleTimeFilterChange("all");
                  handleClearSearch();
                }}
                className="h-6 px-2 text-xs"
              >
                Clear all
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Data Table */}
      {isLoadingDocuments ? (
        <div className="text-center py-8">
          <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
          {searchQuery.trim() ? (
            <>
              <p>No documents found matching "{searchQuery}".</p>
              <p className="text-sm">Try adjusting your search terms or clearing the search filter.</p>
            </>
          ) : timeFilter !== "all" ? (
            <>
              <p>No documents found in the selected time range.</p>
              <p className="text-sm">Try adjusting your filter or selecting a different time range.</p>
            </>
          ) : (
            <>
              <p>No documents in this vault yet.</p>
              <p className="text-sm">Upload documents to get started.</p>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Results Info */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div>
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalDocuments)} of {totalDocuments} documents
            </div>
            {lastStatusRefresh && (
              <div className="flex items-center space-x-1">
                <span>Status last updated:</span>
                <span className="font-medium">
                  {lastStatusRefresh.toLocaleTimeString()}
                </span>
                {loadingStatuses.size > 0 && (
                  <Loader2 className="h-3 w-3 animate-spin ml-2" />
                )}
              </div>
            )}
          </div>

          {/* Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort("name")}
                  >
                    <div className="flex items-center">
                      Document
                      {renderSortIcon("name")}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort("source")}
                  >
                    <div className="flex items-center">
                      Source
                      {renderSortIcon("source")}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort("submit_date")}
                  >
                    <div className="flex items-center">
                      Submit Date
                      {renderSortIcon("submit_date")}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort("status")}
                  >
                    <div className="flex items-center">
                      Status
                      {renderSortIcon("status")}
                    </div>
                  </TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-3">
                          <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                          <div className="min-w-0">
                            <div className="font-medium truncate">{doc.name}</div>
                            {(() => {
                              const statusDetail = getDocumentStatusDetails(doc.id);
                              if (statusDetail?.batch_id) {
                                return (
                                  <div className="text-xs text-muted-foreground">
                                    Batch: {statusDetail.batch_id}
                                  </div>
                                );
                              }
                              return null;
                            })()}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {doc.source || "Unknown"}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex flex-col">
                          <span>{new Date(doc.submit_date).toLocaleDateString()}</span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(doc.submit_date).toLocaleTimeString()}
                          </span>
                        </div>
                        {(() => {
                          const statusDetail = getDocumentStatusDetails(doc.id);
                          if (statusDetail?.batch_started_at && statusDetail?.batch_completed_at) {
                            const startTime = new Date(statusDetail.batch_started_at).getTime();
                            const endTime = new Date(statusDetail.batch_completed_at).getTime();
                            const durationMs = endTime - startTime;
                            const durationSec = Math.round(durationMs / 1000);
                            
                            if (durationSec > 0) {
                              return (
                                <div className="text-xs text-muted-foreground">
                                  Processing: {durationSec < 60 ? `${durationSec}s` : `${Math.round(durationSec / 60)}m`}
                                </div>
                              );
                            }
                          }
                          return null;
                        })()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          {loadingStatuses.has(doc.id) ? (
                            <div className="flex items-center space-x-2">
                              <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                              <Badge variant="secondary" className="opacity-60">
                                {getCurrentDocumentStatus(doc)}
                              </Badge>
                            </div>
                          ) : (
                            <>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Badge variant={getStatusVariant(getCurrentDocumentStatus(doc))}>
                                    {getCurrentDocumentStatus(doc)}
                                  </Badge>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>{getStatusTooltip(getCurrentDocumentStatus(doc))}</p>
                                  {lastStatusRefresh && (
                                    <p className="text-xs opacity-70">
                                      Last updated: {lastStatusRefresh.toLocaleTimeString()}
                                    </p>
                                  )}
                                </TooltipContent>
                              </Tooltip>
                              
                              {isStatusFinal(getCurrentDocumentStatus(doc)) ? (
                                <Tooltip>
                                  <TooltipTrigger>
                                    {renderStatusDetailsDialog(doc)}
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>View detailed processing information</p>
                                  </TooltipContent>
                                </Tooltip>
                              ) : (
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={(e) => handleRefreshDocumentStatus(doc.id, e)}
                                      className="h-5 w-5 p-0 hover:bg-muted"
                                    >
                                      <RefreshCw className="h-3 w-3" />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Click to refresh document status</p>
                                  </TooltipContent>
                                </Tooltip>
                              )}
                            </>
                          )}
                        </div>
                        
                        {/* Additional status information */}
                        {(() => {
                          const statusDetail = getDocumentStatusDetails(doc.id);
                          if (statusDetail) {
                            return (
                              <div className="text-xs text-muted-foreground space-y-0.5">
                                {statusDetail.pipeline_name && (
                                  <div className="flex items-center space-x-1">
                                    <Workflow className="h-3 w-3" />
                                    <span>Pipeline: {statusDetail.pipeline_name}</span>
                                  </div>
                                )}
                                {statusDetail.batch_started_at && (
                                  <div className="flex items-center space-x-1">
                                    <Clock className="h-3 w-3" />
                                    <span>Started: {new Date(statusDetail.batch_started_at).toLocaleString()}</span>
                                  </div>
                                )}
                                {statusDetail.batch_completed_at && (
                                  <div className="flex items-center space-x-1">
                                    <Clock className="h-3 w-3" />
                                    <span>Completed: {new Date(statusDetail.batch_completed_at).toLocaleString()}</span>
                                  </div>
                                )}
                                {!statusDetail.batch_started_at && statusDetail.batch_submitted_at && (
                                  <div className="flex items-center space-x-1">
                                    <Clock className="h-3 w-3" />
                                    <span>Submitted: {new Date(statusDetail.batch_submitted_at).toLocaleString()}</span>
                                  </div>
                                )}
                              </div>
                            );
                          }
                          return null;
                        })()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => onViewProcessingPipeline(doc)}
                        >
                          <Workflow className="h-3 w-3 mr-1" />
                          View Output
                        </Button>
                        {(getCurrentDocumentStatus(doc) === "failed" || getCurrentDocumentStatus(doc) === "error") && (
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => handleRetryProcessing(doc.id)}
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            Retry
                          </Button>
                        )}
                        {getCurrentDocumentStatus(doc) === "pending" && (
                          <Button 
                            size="sm" 
                            onClick={() => onProcessDocument(doc.id)}
                          >
                            <Play className="h-3 w-3 mr-1" />
                            Process
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious 
                      href="#" 
                      onClick={(e) => {
                        e.preventDefault();
                        if (currentPage > 1) handlePageChange(currentPage - 1);
                      }}
                      className={currentPage <= 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                  
                  {/* First page */}
                  {currentPage > 2 && (
                    <PaginationItem>
                      <PaginationLink 
                        href="#" 
                        onClick={(e) => {
                          e.preventDefault();
                          handlePageChange(1);
                        }}
                        className="cursor-pointer"
                      >
                        1
                      </PaginationLink>
                    </PaginationItem>
                  )}
                  
                  {/* Ellipsis */}
                  {currentPage > 3 && (
                    <PaginationItem>
                      <PaginationEllipsis />
                    </PaginationItem>
                  )}
                  
                  {/* Previous page */}
                  {currentPage > 1 && (
                    <PaginationItem>
                      <PaginationLink 
                        href="#" 
                        onClick={(e) => {
                          e.preventDefault();
                          handlePageChange(currentPage - 1);
                        }}
                        className="cursor-pointer"
                      >
                        {currentPage - 1}
                      </PaginationLink>
                    </PaginationItem>
                  )}
                  
                  {/* Current page */}
                  <PaginationItem>
                    <PaginationLink 
                      href="#" 
                      isActive
                      className="cursor-pointer"
                    >
                      {currentPage}
                    </PaginationLink>
                  </PaginationItem>
                  
                  {/* Next page */}
                  {currentPage < totalPages && (
                    <PaginationItem>
                      <PaginationLink 
                        href="#" 
                        onClick={(e) => {
                          e.preventDefault();
                          handlePageChange(currentPage + 1);
                        }}
                        className="cursor-pointer"
                      >
                        {currentPage + 1}
                      </PaginationLink>
                    </PaginationItem>
                  )}
                  
                  {/* Ellipsis */}
                  {currentPage < totalPages - 2 && (
                    <PaginationItem>
                      <PaginationEllipsis />
                    </PaginationItem>
                  )}
                  
                  {/* Last page */}
                  {currentPage < totalPages - 1 && (
                    <PaginationItem>
                      <PaginationLink 
                        href="#" 
                        onClick={(e) => {
                          e.preventDefault();
                          handlePageChange(totalPages);
                        }}
                        className="cursor-pointer"
                      >
                        {totalPages}
                      </PaginationLink>
                    </PaginationItem>
                  )}
                  
                  <PaginationItem>
                    <PaginationNext 
                      href="#" 
                      onClick={(e) => {
                        e.preventDefault();
                        if (currentPage < totalPages) handlePageChange(currentPage + 1);
                      }}
                      className={currentPage >= totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </div>
      )}

      {/* Public method to refresh documents */}
      <div style={{ display: 'none' }} ref={(el) => {
        if (el) {
          (el as any).refreshDocuments = loadVaultDocuments;
          (el as any).refreshStatuses = refreshVisibleDocumentStatuses;
        }
      }} />
      </div>
    </TooltipProvider>
  );
};

export default VaultDocumentsTable;