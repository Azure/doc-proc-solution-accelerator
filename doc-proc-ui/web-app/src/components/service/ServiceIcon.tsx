import React from 'react';
import {
  // Database icons
  Database,
  // AI/ML icons
  Brain,
  Bot,
  Zap,
  // Storage icons
  HardDrive,
  Cloud,
  Archive,
  // Search icons
  Search,
  // Integration icons
  Link,
  Webhook,
  Globe,
  // Analytics icons
  BarChart3,
  TrendingUp,
  PieChart,
  // Monitoring icons
  Activity,
  Eye,
  AlertCircle,
  // Generic icons
  Server,
  Settings,
  Package,
  Layers,
  // Communication icons
  MessageSquare,
  Mail,
  // Security icons
  Shield,
  Key,
  Lock,
  Container,
} from 'lucide-react';

import { cn } from '@/lib/utils';

interface ServiceIconProps {
  iconName?: string;
  className?: string;
  size?: number;
}

// Map icon names to Lucide React components
const iconMap: Record<string, React.ComponentType<any>> = {
  // Database
  database: Database,
  'database-2': Database,
  sql: Database,
  mongodb: Database,
  postgresql: Database,
  mysql: Database,
  cosmosdb: Database,
  
  // AI/ML
  brain: Brain,
  ai: Brain,
  'artificial-intelligence': Brain,
  bot: Bot,
  robot: Bot,
  openai: Bot,
  'azure-openai': Bot,
  anthropic: Bot,
  claude: Bot,
  gpt: Bot,
  llm: Bot,
  'machine-learning': Brain,
  ml: Brain,
  'vertex-ai': Brain,
  'azure-ai': Brain,
  cognitive: Brain,
  lightning: Zap,
  spark: Zap,
  
  // Storage
  storage: Container,
  'hard-drive': HardDrive,
  disk: HardDrive,
  container: Container,
  cloud: Cloud,
  'cloud-storage': Container,
  blob: Container,
  's3': Container,
  'data-lake': Archive,
  archive: Archive,
  backup: Archive,
  
  // Search
  search: Search,
  elasticsearch: Search,
  'azure-search': Search,
  'cognitive-search': Search,
  solr: Search,
  lucene: Search,
  
  // Integration
  integration: Link,
  link: Link,
  connector: Link,
  webhook: Webhook,
  api: Globe,
  rest: Globe,
  graphql: Globe,
  'service-bus': MessageSquare,
  'message-queue': MessageSquare,
  'logic-apps': Layers,
  workflow: Layers,
  
  // Analytics
  analytics: BarChart3,
  'bar-chart': BarChart3,
  chart: BarChart3,
  dashboard: BarChart3,
  'power-bi': PieChart,
  tableau: TrendingUp,
  looker: TrendingUp,
  synapse: BarChart3,
  'data-warehouse': BarChart3,
  
  // Monitoring
  monitoring: Activity,
  metrics: Activity,
  telemetry: Activity,
  logs: Eye,
  observability: Eye,
  'application-insights': Eye,
  'azure-monitor': Activity,
  grafana: Activity,
  prometheus: Activity,
  alert: AlertCircle,
  notification: AlertCircle,
  
  // Communication
  email: Mail,
  smtp: Mail,
  sendgrid: Mail,
  'microsoft-graph': MessageSquare,
  teams: MessageSquare,
  slack: MessageSquare,
  
  // Security
  security: Shield,
  auth: Shield,
  authentication: Shield,
  authorization: Shield,
  'azure-ad': Shield,
  'active-directory': Shield,
  key: Key,
  'api-key': Key,
  secret: Lock,
  vault: Lock,
  'key-vault': Lock,
  
  // Generic/Fallback
  server: Server,
  service: Server,
  component: Package,
  module: Package,
  plugin: Package,
  extension: Package,
  settings: Settings,
  config: Settings,
  configuration: Settings,
  layer: Layers,
  stack: Layers,
};

// Get category-based fallback icon
const getCategoryIcon = (category?: string): React.ComponentType<any> => {
  if (!category) return Server;
  
  const categoryLower = category.toLowerCase();
  
  if (categoryLower.includes('data') || categoryLower.includes('database')) return Database;
  if (categoryLower.includes('ai') || categoryLower.includes('ml') || categoryLower.includes('intelligence')) return Brain;
  if (categoryLower.includes('storage')) return HardDrive;
  if (categoryLower.includes('search')) return Search;
  if (categoryLower.includes('integration')) return Link;
  if (categoryLower.includes('analytics')) return BarChart3;
  if (categoryLower.includes('monitoring')) return Activity;
  if (categoryLower.includes('security')) return Shield;
  
  return Server;
};

// Get type-based fallback icon
const getTypeIcon = (type?: string): React.ComponentType<any> => {
  if (!type) return Server;
  
  const typeLower = type.toLowerCase();
  
  if (typeLower.includes('database') || typeLower.includes('db')) return Database;
  if (typeLower.includes('ai') || typeLower.includes('ml') || typeLower.includes('intelligence')) return Brain;
  if (typeLower.includes('storage')) return HardDrive;
  if (typeLower.includes('search')) return Search;
  if (typeLower.includes('integration')) return Link;
  if (typeLower.includes('analytics')) return BarChart3;
  if (typeLower.includes('monitoring')) return Activity;
  if (typeLower.includes('security')) return Shield;
  
  return Server;
};

export const ServiceIcon: React.FC<ServiceIconProps & { category?: string; type?: string }> = ({ 
  iconName, 
  category,
  type,
  className, 
  size = 16 
}) => {
  let IconComponent: React.ComponentType<any>;

  if (iconName) {
    // Try exact match first
    IconComponent = iconMap[iconName.toLowerCase()];
    
    // If no exact match, try partial matches
    if (!IconComponent) {
      const iconKey = Object.keys(iconMap).find(key => 
        iconName.toLowerCase().includes(key) || key.includes(iconName.toLowerCase())
      );
      IconComponent = iconKey ? iconMap[iconKey] : undefined;
    }
  }

  // Fallback to category or type-based icon
  if (!IconComponent) {
    if (category) {
      IconComponent = getCategoryIcon(category);
    } else if (type) {
      IconComponent = getTypeIcon(type);
    } else {
      IconComponent = Server;
    }
  }

  return (
    <IconComponent 
      className={cn("flex-shrink-0", className)} 
      size={size}
    />
  );
};

export default ServiceIcon;
