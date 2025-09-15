
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  RefreshCw
} from "lucide-react";

interface ExecutionMetric {
  id: string;
  timestamp: string;
  duration: number;
  status: 'success' | 'failed' | 'warning';
  documentsProcessed: number;
  stepMetrics: {
    stepName: string;
    duration: number;
    status: 'success' | 'failed' | 'warning';
    throughput?: number;
  }[];
}

const PipelineMetrics = () => {
  const [timeRange, setTimeRange] = useState("24h");
  const [executions] = useState<ExecutionMetric[]>([
    {
      id: "1",
      timestamp: "2024-06-23T10:30:00Z",
      duration: 245,
      status: "success",
      documentsProcessed: 12,
      stepMetrics: [
        { stepName: "Document Ingestion", duration: 45, status: "success", throughput: 0.27 },
        { stepName: "Entity Extraction", duration: 120, status: "success", throughput: 0.1 },
        { stepName: "AI Summarization", duration: 65, status: "success", throughput: 0.18 },
        { stepName: "Database Storage", duration: 15, status: "success", throughput: 0.8 }
      ]
    },
    {
      id: "2", 
      timestamp: "2024-06-23T09:15:00Z",
      duration: 180,
      status: "failed",
      documentsProcessed: 8,
      stepMetrics: [
        { stepName: "Document Ingestion", duration: 30, status: "success", throughput: 0.27 },
        { stepName: "Entity Extraction", duration: 90, status: "success", throughput: 0.09 },
        { stepName: "AI Summarization", duration: 60, status: "failed", throughput: 0 },
        { stepName: "Database Storage", duration: 0, status: "failed", throughput: 0 }
      ]
    }
  ]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800">Success</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Calculate summary metrics
  const totalExecutions = executions.length;
  const successfulExecutions = executions.filter(e => e.status === 'success').length;
  const failedExecutions = executions.filter(e => e.status === 'failed').length;
  const averageDuration = executions.reduce((acc, e) => acc + e.duration, 0) / totalExecutions;
  const totalDocuments = executions.reduce((acc, e) => acc + e.documentsProcessed, 0);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalExecutions}</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round((successfulExecutions / totalExecutions) * 100)}%</div>
            <p className="text-xs text-muted-foreground">{successfulExecutions}/{totalExecutions} successful</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(Math.round(averageDuration))}</div>
            <p className="text-xs text-muted-foreground">Per execution</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents Processed</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDocuments}</div>
            <p className="text-xs text-muted-foreground">Total documents</p>
          </CardContent>
        </Card>
      </div>

      {/* Execution History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Execution History</CardTitle>
              <CardDescription>Recent pipeline execution results</CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last Hour</SelectItem>
                  <SelectItem value="24h">Last 24h</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {executions.map((execution) => (
              <div key={execution.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(execution.status)}
                    <div>
                      <p className="font-medium">{formatTimestamp(execution.timestamp)}</p>
                      <p className="text-sm text-muted-foreground">
                        {execution.documentsProcessed} documents • {formatDuration(execution.duration)}
                      </p>
                    </div>
                  </div>
                  {getStatusBadge(execution.status)}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {execution.stepMetrics.map((step, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-muted rounded">
                      <div>
                        <p className="text-sm font-medium">{step.stepName}</p>
                        <p className="text-xs text-muted-foreground">{formatDuration(step.duration)}</p>
                      </div>
                      {getStatusIcon(step.status)}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineMetrics;