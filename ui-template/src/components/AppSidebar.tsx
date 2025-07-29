
import { LayoutDashboard, Vault, Settings, Link, Workflow, Puzzle, Server, Cog } from "lucide-react";
import { Link as RouterLink, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar";

const navigationItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Vaults",
    url: "/vaults",
    icon: Vault,
  },
  {
    title: "Vaults2",
    url: "/vaults2",
    icon: Vault,
  },
  {
    title: "Vaults3",
    url: "/vaults3",
    icon: Vault,
  },
  {
    title: "Vaults4",
    url: "/vaults4",
    icon: Vault,
  },
  {
    title: "Vaults5",
    url: "/vaults5",
    icon: Vault,
  },
  {
    title: "Vaults6",
    url: "/vaults6",
    icon: Vault,
  },  
  {
    title: "App Connections",
    url: "/connections",
    icon: Link,
  },

];

const processingItems = [
  {
    title: "Pipelines",
    url: "/pipeline",
    icon: Workflow,
  },
  {
    title: "Pipelines2",
    url: "/pipeline2",
    icon: Workflow,
  },
  {
    title: "Pipeline Config",
    url: "/pipeline-config",
    icon: Cog,
  },
  {
    title: "Steps",
    url: "/steps",
    icon: Puzzle,
  },
  {
    title: "Services",
    url: "/services",
    icon: Server,
  },
];

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <div className="flex items-center space-x-2">
          <Settings className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">Doc-Proc</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>App</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location.pathname === item.url}>
                    <RouterLink to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </RouterLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        
        <SidebarGroup>
          <SidebarGroupLabel>Configure</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {processingItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location.pathname === item.url}>
                    <RouterLink to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </RouterLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
