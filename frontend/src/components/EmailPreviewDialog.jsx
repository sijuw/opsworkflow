import {
    Mail,
    Users,
    Paperclip,
    Send,
    Loader2,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

function EmailPreviewDialog({
  open,
  onOpenChange,
  preview,
  attachSamples,
  onConfirm,
  sending,
}) {
  // Nothing is reconstructed here: `preview` is the rendered email the
  // server will send, so what is approved below is what goes out.
  const subject = preview?.subject ?? "";
  const to = preview?.to ?? [];
  const cc = preview?.cc ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Email Preview</DialogTitle>
          <DialogDescription>
            Review the exact notification before sending it out.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Email Details */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900/50">
            <h3 className="mb-4 flex items-center gap-2 font-semibold dark:text-slate-100">
              <Mail className="h-5 w-5" />
              Email Details
            </h3>

            <div className="space-y-3 text-sm">
              <div>
                <p className="text-slate-500 dark:text-slate-400">
                  Subject: <span className="font-medium text-slate-900 dark:text-slate-100">{subject}</span>
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                <p className="text-slate-500 dark:text-slate-400">
                  To: <span className="font-medium text-slate-900 dark:text-slate-100">
                    {to.length ? to.join(", ") : "No email provided"}
                  </span>
                </p>
              </div>

              {cc.length > 0 && (
                <div className="flex items-center gap-2 pl-6">
                  <p className="text-slate-500 dark:text-slate-400">
                    CC: <span className="font-medium text-slate-900 dark:text-slate-100">
                      {cc.join(", ")}
                    </span>
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Attachment Preview Block */}
          {attachSamples && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900/50">
                <h3 className="mb-4 flex items-center gap-2 font-semibold dark:text-slate-100">
                <Paperclip className="h-5 w-5" />
                Attachment Preview
                </h3>

                <div className="space-y-2 text-sm">
                <p className="font-medium text-slate-900 dark:text-slate-100">
                    {preview?.attachment_name}
                </p>

                <p className="text-slate-600 dark:text-slate-300">
                    {preview?.sample_count ?? 0} sample transactions
                </p>

                <div>
                    <p className="text-slate-500 dark:text-slate-400">
                    Latest Transaction
                    </p>

                    <p className="font-medium dark:text-slate-200">
                    {preview?.latest_transaction || "No transactions found"}
                    </p>
                </div>
                </div>
            </div>
          )}

          {/* The rendered body, shown exactly as the recipient will see it.
              Sandboxed so the preview can't execute anything. */}
          <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-800">
            <iframe
              title="Email body preview"
              srcDoc={preview?.body ?? ""}
              sandbox=""
              className="h-64 w-full bg-white"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={sending}
            className="dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancel
          </Button>

          <Button
            onClick={onConfirm}
            disabled={sending}
            className="bg-[#007cc2] hover:bg-[#0056b3]/50 text-white dark:bg-[#007cc2] dark:hover:bg-[#0056b3]"
          >
            {sending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Confirm & Send
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default EmailPreviewDialog;
