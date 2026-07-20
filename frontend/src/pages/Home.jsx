import WorkflowCard from "@/components/WorkflowCard";
import { 
  Mail, 
  ScrollText, 
  RefreshCw, 
  Network, 
  BarChart3, 
  Activity,
  ServerCog,
  Settings, // Added for Admin module
} from "lucide-react";
import PageContainer from "@/components/layout/PageContainer";

function Home() {
  return (
    <PageContainer maxWidth="6xl">
      <div className="space-y-12">
        
        {/* Header */}
        <div className="mb-12 flex flex-col items-center text-center">
          <h1 className="flex items-center gap-3 text-4xl font-bold text-slate-900 dark:text-white">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#007cc2]/10 text-[#007cc2] dark:bg-[#007cc2]/20 dark:text-[#3399ff]">
              <ServerCog className="h-6 w-6" />
            </div>
            Switch SRE Workflow
          </h1>
          <p className="mt-3 text-lg text-slate-500 dark:text-slate-400">
             Internal SRE Support Portal
          </p>
        </div>
        

        {/* Section: Operational Automation */}
        <section>
          <div className="mb-6 border-b border-slate-200 dark:border-slate-800 pb-2">
            <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
              Operational Automation
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <WorkflowCard
              title="Email Notification"
              description="Send standardized incident notifications to partner institutions."
              icon={Mail}
              status="available"
              to="/email"
            />
            <WorkflowCard
              title="Switch Bank VPN"
              description="Switch VPN connections for partner banks."
              icon={Network}
              status="planned"
            />
            <WorkflowCard
              title="Refresh Interchange"
              description="Refresh interchange configurations."
              icon={RefreshCw}
              status="planned"
            />
          </div>
        </section>

        {/* Section: Observability */}
        <section>
          <div className="mb-6 border-b border-slate-200 dark:border-slate-800 pb-2">
            <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
              Observability
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <WorkflowCard
              title="Enable Logging"
              description="Enable debug logging on backend services."
              icon={ScrollText}
              status="planned"
            />
            <WorkflowCard
              title="Check Status"
              description="Check the status of various products."
              icon={Activity}
              status="planned"
            />
          </div>
        </section>

        {/* Section: Reporting */}
        <section>
          <div className="mb-6 border-b border-slate-200 dark:border-slate-800 pb-2">
            <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
              Reporting
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <WorkflowCard
              title="Generate Reports"
              description="Generate operational and incident reports."
              icon={BarChart3}
              status="planned"
            />
          </div>
        </section>

        {/* Section: Admin & Configuration */}
        <section>
          <div className="mb-6 border-b border-slate-200 dark:border-slate-800 pb-2">
            <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
              Admin & Configuration
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <WorkflowCard
              title="Institution Management"
              description="Manage bank details, IDs, and notification contacts."
              icon={Settings}
              status="available"
              to="/admin/institutions"
            />
          </div>
        </section>

      </div>
    </PageContainer>
  );
}

export default Home;