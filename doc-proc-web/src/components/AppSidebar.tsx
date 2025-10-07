
import { LayoutDashboard, Vault, Settings, Link, Workflow, Puzzle, Server, Cog, Database } from "lucide-react";
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
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
} from "@/components/ui/sidebar";
import { OnlineStatusIndicator } from "@/components/OnlineStatusIndicator";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";

const appNavigationItems = [
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
    title: "App Health",
    url: "/health",
    icon: Link,
  },

];

const appConfigItems = [
  {
    title: "Pipelines",
    url: "/pipeline",
    icon: Workflow,
  },
  {
    title: "Steps",
    url: "/steps",
    icon: Puzzle,
    subItems: [
      {
        title: "Step Instances",
        url: "/step-instances",
        icon: Database,
      },
    ],
  },
  {
    title: "Services",
    url: "/services",
    icon: Server,
    subItems: [
      {
        title: "Service Instances",
        url: "/service-instances",
        icon: Database,
      },
    ],
  },
  {
    title: "Sources",
    url: "/sources",
    icon: Database,
    subItems: [
      {
        title: "Source Instances",
        url: "/source-instances",
        icon: Database,
      },
    ],
  }
];

export function AppSidebar() {
  const location = useLocation();
  const onlineStatus = useOnlineStatus({ checkInterval: 60000 });

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
              {appNavigationItems.map((item) => (
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
              {appConfigItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location.pathname === item.url}>
                    <RouterLink to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </RouterLink>
                  </SidebarMenuButton>

                  {item.subItems && (
                    <SidebarMenuSub>
                      {item.subItems.map((subItem) => (
                        <SidebarMenuSubItem key={subItem.title}>
                          <SidebarMenuSubButton asChild isActive={location.pathname === subItem.url}>
                            <RouterLink to={subItem.url}>
                            <subItem.icon />
                            <span>{subItem.title}</span>
                          </RouterLink>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                    )}
                  
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      {/* Online Status Indicator at bottom */}
      <div className="border-t px-6 py-3">
        <OnlineStatusIndicator 
          status={onlineStatus}
          onRefresh={onlineStatus.refresh}
          size="sm"
          showText={true}
          className="justify-center"
        />
      </div>
    </Sidebar>
  );
}
