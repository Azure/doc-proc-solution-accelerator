
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Activity, FileText, HardDrive, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";

const Dashboard = () => {
  const stats = [
    {
      title: "Total Vaults",
      value: "12",
      change: "+2 this month",
      icon: HardDrive,
    },
    {
      title: "Documents Processed",
      value: "2,847",
      change: "+18% from last month",
      icon: FileText,
    },
    {
      title: "Processing Queue",
      value: "23",
      change: "5 in progress",
      icon: Activity,
    },
    {
      title: "Success Rate",
      value: "98.4%",
      change: "+0.3% improvement",
      icon: TrendingUp,
    },
  ];

  const recentActivity = [
    { action: "Document uploaded", vault: "Legal Documents", time: "2 minutes ago", status: "processing" },
    { action: "Chunking completed", vault: "Research Papers", time: "5 minutes ago", status: "completed" },
    { action: "Processing failed", vault: "Marketing Materials", time: "12 minutes ago", status: "error" },
    { action: "Vault created", vault: "Product Specs", time: "1 hour ago", status: "completed" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Monitor your document processing system performance and activity.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Processing Status</CardTitle>
            <CardDescription>Current system processing overview</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Documents in Queue</span>
                <span>23/100</span>
              </div>
              <Progress value={23} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Processing Capacity</span>
                <span>78%</span>
              </div>
              <Progress value={78} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Storage Usage</span>
                <span>45/100 GB</span>
              </div>
              <Progress value={45} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest system events and updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {activity.status === "completed" && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {activity.status === "processing" && (
                      <Activity className="h-4 w-4 text-blue-500" />
                    )}
                    {activity.status === "error" && (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{activity.action}</p>
                    <p className="text-xs text-muted-foreground">{activity.vault}</p>
                  </div>
                  <div className="flex-shrink-0">
                    <Badge
                      variant={
                        activity.status === "completed"
                          ? "default"
                          : activity.status === "error"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {activity.status}
                    </Badge>
                  </div>
                  <div className="flex-shrink-0 text-xs text-muted-foreground">
                    {activity.time}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
