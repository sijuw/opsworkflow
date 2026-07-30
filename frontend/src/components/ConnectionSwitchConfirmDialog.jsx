import { ArrowRight, Loader2, Network, ShieldCheck } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

/**
 * Everything shown here comes from /connections/switch/preview, which runs the same
 * code path as the switch itself — including the diff assertion. Nothing is
 * recomputed client-side, so what is approved is what gets sent.
 */
function ConnectionSwitchConfirmDialog({
  open,
  onOpenChange,
  preview,
  onConfirm,
  switching,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Confirm connection switch</DialogTitle>
          <DialogDescription>
            Review the exact change before it is applied in Cosmos.
          </DialogDescription>
        </DialogHeader>

        {preview && (
          <div className="space-y-5">
            {/* Route transition */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900/50">
              <h3 className="mb-4 flex items-center gap-2 font-semibold dark:text-slate-100">
                <Network className="h-5 w-5" />
                {preview.institution_name}
                <span className="text-sm font-normal text-slate-500 dark:text-slate-400">
                  · interchange {preview.interchange_id}
                </span>
              </h3>

              {/* The medium is the headline. Route names alone are
                  ambiguous: PRIMARY is a GCP VPN for most institutions but a
                  leased line for NIBSS. */}
              <div className="flex items-center gap-3">
                <span className="rounded-md bg-white px-3 py-1.5 text-base font-semibold text-slate-800 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:ring-slate-700">
                  {preview.from_medium_label}
                </span>
                <ArrowRight className="h-5 w-5 text-slate-400" />
                <span className="rounded-md bg-[#007cc2]/10 px-3 py-1.5 text-base font-semibold text-[#007cc2] dark:bg-[#007cc2]/20 dark:text-[#3399ff]">
                  {preview.to_medium_label}
                </span>
              </div>

              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                {preview.from_route} → {preview.to_route}
                {preview.to_medium_note ? ` · ${preview.to_medium_note}` : ""}
              </p>

              {/* Medium is human-maintained metadata; OpsFlow cannot verify
                  that a port really egresses via GCP. Show its age so stale
                  labels do not pass as fact. */}
              {preview.to_medium_updated_at && (
                <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  Medium as configured — last updated{" "}
                  {new Date(preview.to_medium_updated_at).toLocaleDateString()}
                </p>
              )}
            </div>

            {/* The diff */}
            <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
              <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium text-slate-500 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-400">
                {preview.changed_field}
              </div>

              <div className="bg-white font-mono text-xs dark:bg-slate-950">
                <div className="flex gap-2 border-b border-slate-100 px-4 py-2 text-red-700 dark:border-slate-900 dark:text-red-400">
                  <span className="select-none opacity-60">-</span>
                  <span className="break-all">{preview.before}</span>
                </div>
                <div className="flex gap-2 px-4 py-2 text-green-700 dark:text-green-400">
                  <span className="select-none opacity-60">+</span>
                  <span className="break-all">{preview.after}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 border-t border-slate-200 bg-slate-50 px-4 py-2 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-400">
                <ShieldCheck className="h-3.5 w-3.5 text-green-600 dark:text-green-500" />
                1 field changed · {preview.fields_untouched} fields untouched
              </div>
            </div>

            {/* Where it goes */}
            <div className="rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-500 dark:bg-slate-900/50 dark:text-slate-400">
              <span className="font-medium text-slate-600 dark:text-slate-300">
                POST
              </span>{" "}
              {preview.target_service}
              <span className="break-all">{preview.target_path}</span>
            </div>

            {preview.note && (
              <p className="text-sm text-amber-700 dark:text-amber-400">
                {preview.note}
              </p>
            )}
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={switching}
            className="dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancel
          </Button>

          <Button
            onClick={onConfirm}
            disabled={switching || !preview}
            className="bg-[#007cc2] text-white hover:bg-[#0056b3]/80 dark:bg-[#007cc2] dark:hover:bg-[#0056b3]"
          >
            {switching ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Switching...
              </>
            ) : (
              <>
                <Network className="mr-2 h-4 w-4" />
                Confirm switch
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ConnectionSwitchConfirmDialog;
