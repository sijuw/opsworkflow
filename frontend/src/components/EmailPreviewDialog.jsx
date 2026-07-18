import {
    Mail,
    Building2, // You can remove this if you aren't using it
    Users,
    Paperclip,
    FileText,  // You can remove this if you aren't using it
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
  attachmentName, // Comes directly from the backend now!
}) {
  const today = new Date();
  const dateString =
    today.getFullYear() +
    String(today.getMonth() + 1).padStart(2, "0") +
    String(today.getDate()).padStart(2, "0");
  const rcStr = responseCode || "N/A";
  const subjectLine = `${institution?.name || "Institution"} | ATS | RC${rcStr} | ${dateString}`;

  // REMOVED the duplicate const attachmentName declaration here

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
          <div className="rounded-xl border bg-slate-50 p-5">
            <h3 className="mb-4 flex items-center gap-2 font-semibold">
              <Mail className="h-5 w-5" />
              Email Details
            </h3>

            <div className="space-y-3 text-sm">
              <div>
                <p className="text-slate-500">
                  Subject: <span className="font-medium text-slate-900">{subjectLine}</span>
                </p>
              </div>

              {/* Updated To: Line */}
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-slate-500" />
                <p className="text-slate-500">
                  To: <span className="font-medium text-slate-900">
                    {institution?.email_to 
                        ? institution.email_to.split(",").map(e => e.trim()).join(", ") 
                        : "No email provided"}
                  </span>
                </p>
              </div>

              {/* Updated CC: Line */}
              {institution?.email_cc && (
                <div className="flex items-center gap-2 pl-6">
                  <p className="text-slate-500">
                    CC: <span className="font-medium text-slate-900">
                      {institution.email_cc.split(",").map(e => e.trim()).join(", ")}
                    </span>
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* New Attachment Preview Block */}
          {attachSamples && (
            <div className="rounded-xl border bg-slate-50 p-5">
                <h3 className="mb-4 flex items-center gap-2 font-semibold">
                <Paperclip className="h-5 w-5" />
                Attachment Preview
                </h3>

                <div className="space-y-2 text-sm">
                <p className="font-medium text-slate-900">
                    {attachmentName}
                </p>

                <p className="text-slate-600">
                    {sampleCount ?? 0} sample transactions
                </p>

                <div>
                    <p className="text-slate-500">
                    Latest Transaction
                    </p>

                    <p className="font-medium">
                    {latestTransaction || "No transactions found"}
                    </p>
                </div>
                </div>
            </div>
          )}

          <div className="rounded-md border bg-slate-50 p-4 text-sm">
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
                  <strong>Additional Context:</strong>
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
              <strong>Application Support Team</strong>
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={sending}
          >
            Cancel
          </Button>

          <Button
            onClick={onConfirm}
            disabled={sending}
            className="bg-[#007cc2] hover:bg-[#0056b3]/50 text-white"
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