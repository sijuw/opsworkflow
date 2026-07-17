import { Mail } from "lucide-react";

export default function Header() {
  return (
    <div className="border-b bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            OpsFlow
          </h1>

          <p className="text-sm text-slate-500">
            Internal Operations Portal
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2">
          <Mail className="h-5 w-5 text-blue-600" />
          <span className="font-medium">
            Email Notification
          </span>
        </div>
      </div>
    </div>
  );
}