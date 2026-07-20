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
  institution,
  responseCode,
  comments,
  attachSamples,
  onConfirm,
  sending, 
  sampleCount,
  latestTransaction,
  attachmentName, 
}) {
  const today = new Date();
  const dateString =
    today.getFullYear() +
    String(today.getMonth() + 1).padStart(2, "0") +
    String(today.getDate()).padStart(2, "0");
  const rcStr = responseCode || "N/A";
  const subjectLine = `${institution?.name || "Institution"} | ATS | RC${rcStr} | ${dateString}`;

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
                  Subject: <span className="font-medium text-slate-900 dark:text-slate-100">{subjectLine}</span>
                </p>
              </div>

              {/* Updated To: Line */}
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                <p className="text-slate-500 dark:text-slate-400">
                  To: <span className="font-medium text-slate-900 dark:text-slate-100">
                    {institution?.email_to 
                        ? institution.email_to.split(",").map(e => e.trim()).join(", ") 
                        : "No email provided"}
                  </span>
                </p>
              </div>

              {/* Updated CC: Line */}
              {institution?.email_cc && (
                <div className="flex items-center gap-2 pl-6">
                  <p className="text-slate-500 dark:text-slate-400">
                    CC: <span className="font-medium text-slate-900 dark:text-slate-100">
                      {institution.email_cc.split(",").map(e => e.trim()).join(", ")}
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
                    {attachmentName}
                </p>

                <p className="text-slate-600 dark:text-slate-300">
                    {sampleCount ?? 0} sample transactions
                </p>

                <div>
                    <p className="text-slate-500 dark:text-slate-400">
                    Latest Transaction
                    </p>

                    <p className="font-medium dark:text-slate-200">
                    {latestTransaction || "No transactions found"}
                    </p>
                </div>
                </div>
            </div>
          )}

          {/* Email Body Context */}
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-300">
            <p>Hello team,</p>
            <br />
            <p>
              Please be informed that {institution?.name || "Institution"} bank
              card transactions are currently failing with RC{rcStr}.
            </p>

            {comments && (
              <>
                <br />
                <p>
                  <strong className="dark:text-slate-100">Additional Context:</strong>
                  <br />
                  {comments}
                </p>
              </>
            )}

            <br />
            <p>Kindly assist with the review.</p>

            {attachSamples && (
              <p>
                <br />
                Please find attached sample transactions for your investigation.
              </p>
            )}

            <br />
            <br />
            <p>Thanks and warm regards,</p>
            <p>
              <strong className="dark:text-slate-100">Application Support Team</strong>
            </p>
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