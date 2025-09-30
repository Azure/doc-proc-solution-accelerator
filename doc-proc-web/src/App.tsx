
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import AppLayout from "@/components/AppLayout";
import Dashboard from "@/pages/Dashboard";
import Vaults from "@/pages/Vaults";
import Vaults4 from "@/pages/Vaults4";
import Health from "@/pages/Health";
import Pipeline from "@/pages/Pipeline";
import Step from "@/pages/Steps";
import StepInstances from "@/pages/StepInstances";
import Service from "@/pages/Services";
import ServiceInstances from "@/pages/ServiceInstances";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <SidebarProvider>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="vaults" element={<Vaults />} />
              <Route path="vaults4" element={<Vaults4 />} />
              <Route path="pipeline" element={<Pipeline />} />
              <Route path="steps" element={<Step />} />
              <Route path="step-instances" element={<StepInstances />} />
              <Route path="services" element={<Service />} />
              <Route path="service-instances" element={<ServiceInstances />} />
              <Route path="health" element={<Health />} />
              
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </SidebarProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
