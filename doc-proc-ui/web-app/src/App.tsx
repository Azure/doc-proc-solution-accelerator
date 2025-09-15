
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Vaults from "./pages/Vaults";
import Vaults2 from "./pages/Vaults2";
import Vaults3 from "./pages/Vaults3";
import Vaults4 from "./pages/Vaults4";
import Vaults5 from "./pages/Vaults5";
import Vaults6 from "./pages/Vaults6";
import Connections from "./pages/Connections";
import Pipeline from "./pages/Pipeline";
import Pipeline2 from "./pages/Pipeline2";
import PipelineConfigDemo from "./pages/PipelineConfigDemo";
import Step from "./pages/Steps";
import StepInstances from "./pages/StepInstances";
import Service from "./pages/Services";
import ServiceInstances from "./pages/ServiceInstances";
import NotFound from "./pages/NotFound";

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
              <Route path="vaults2" element={<Vaults2 />} />
              <Route path="vaults3" element={<Vaults3 />} />
              <Route path="vaults4" element={<Vaults4 />} />
              <Route path="vaults5" element={<Vaults5 />} />
              <Route path="vaults6" element={<Vaults6 />} />
              <Route path="pipeline" element={<Pipeline />} />
              <Route path="pipeline2" element={<Pipeline2 />} />
              <Route path="pipeline-config" element={<PipelineConfigDemo />} />
              <Route path="steps" element={<Step />} />
              <Route path="step-instances" element={<StepInstances />} />
              <Route path="services" element={<Service />} />
              <Route path="service-instances" element={<ServiceInstances />} />
              <Route path="connections" element={<Connections />} />
              
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </SidebarProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
