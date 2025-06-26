
import { LayoutDashboard, Vault, Settings, Link, Workflow, Puzzle, Server } from "lucide-react";
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

const menuItems = [
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
    title: "Steps",
    url: "/steps",
    icon: Puzzle,
  },
  {
    title: "Services",
    url: "/services",
    icon: Server,
  },
  {
    title: "App Connections",
    url: "/connections",
    icon: Link,
  },

];

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <div className="flex items-center space-x-2">
          <Settings className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">DocProcessor</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
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
