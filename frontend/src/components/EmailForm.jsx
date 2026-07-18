import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Mail, Send, Loader2 } from "lucide-react";
import InstitutionSelect from "./InstitutionSelect";
import ResponseCodeSelect from "./ResponseCodeSelect";
import AttachSamplesCheckbox from "./AttachSamplesCheckbox";
import CommentsBox from "./CommentsBox";
import EmailPreviewDialog from "./EmailPreviewDialog";

import {
    getInstitutions,
    getResponseCodes,
    sendEmail,
    previewEmail
} from "../services/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

function EmailForm() {
    const [institutions, setInstitutions] = useState([]);
    const [responseCodes, setResponseCodes] = useState([]);
    
    // 1. Added previewData to state
    const [previewData, setPreviewData] = useState(null); 
    const [previewOpen, setPreviewOpen] = useState(false);
    const [loadingPreview, setLoadingPreview] = useState(false);

    const [institution, setInstitution] = useState("");
    const [responseCode, setResponseCode] = useState("");
    const [attachSamples, setAttachSamples] = useState(true);
    const [comments, setComments] = useState("");
    const [sending, setSending] = useState(false);

    useEffect(() => {
        loadInstitutions();
        loadResponseCodes();
    }, []);

    async function loadInstitutions() {
        try {
            const response = await getInstitutions();
            setInstitutions(response.data);
        } catch (error) {
            console.error("Failed to load institutions:", error);
            toast.error("Failed to load institutions from the server.");
        }
    }

    async function loadResponseCodes() {
        try {
            const response = await getResponseCodes();
            setResponseCodes(response.data);
        } catch (error) {
            console.error("Failed to load response codes:", error);
            toast.error("Failed to load response codes from the server.");
        }
    }

    async function handlePreview() {
        if (!institution) {
            // 2. Swapped to toast
            toast.warning("Please select an institution.");
            return;
        }

        try {
            setLoadingPreview(true);

            const response = await previewEmail({
                institution_id: Number(institution),
                response_code: responseCode || null,
                attach_samples: attachSamples, // 3. Added the missing parameter
            });

            setPreviewData(response.data);
            setPreviewOpen(true);

        } catch (error) {
            console.error(error);
            // 2. Swapped to toast
            toast.error("Unable to generate preview.");
        } finally {
            setLoadingPreview(false);
        }
    }

    async function confirmAndSendEmail() {
        if (!institution) {
            toast.warning("Please select an institution.");
            return;
        }

        try {
            setSending(true);

            await sendEmail({
                institution_id: Number(institution),
                response_code: responseCode || null,
                attach_samples: attachSamples,
                comments: comments,
            });

            toast.success("Email sent successfully!");
            setComments("");
            
            // Close the preview dialog if it was open
            setPreviewOpen(false);

        } catch (error) {
            console.error(error);
            toast.error("Failed to send email. Please try again.");
        } finally {
            setSending(false);
        }
    }

    return (
        <Card className="rounded-2xl border border-slate-200 shadow-xl">
            <CardHeader>
            <div className="flex items-center gap-4">
                {/* Colorful Icon Container */}
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#007cc2]/10 text-[#007cc2]">
                    <Mail className="h-6 w-6" />
                </div>
                
                {/* Text container */}
                <div className="flex flex-col">
                <CardTitle className="text-2xl">SRE Email Notification Portal</CardTitle>
                <p className="text-sm text-slate-500 font-normal">
                    Notify partner institutions about transaction issues.
                </p>
                </div>
            </div>
            </CardHeader>
            
            <CardContent className="space-y-6 pt-4">
                <InstitutionSelect
                    institutions={institutions}
                    value={institution}
                    onChange={setInstitution}
                />

                <ResponseCodeSelect
                    responseCodes={responseCodes}
                    value={responseCode}
                    onChange={setResponseCode}
                />

                <CommentsBox
                    value={comments}
                    onChange={setComments}
                />

                <AttachSamplesCheckbox
                    checked={attachSamples}
                    onChange={setAttachSamples}
                />
                
                <EmailPreviewDialog
                    open={previewOpen}
                    onOpenChange={setPreviewOpen}
                    institution={
                        institutions.find(
                            (i) => i.id === Number(institution)
                        )
                    }
                    responseCode={responseCode}
                    comments={comments}
                    attachSamples={attachSamples}
                    onConfirm={confirmAndSendEmail}
                    sending={sending}
                    sampleCount={previewData?.sample_count}
                    latestTransaction={previewData?.latest_transaction}
                    attachmentName={previewData?.attachment_name}
                />
                
                <div className="flex flex-row gap-4 pt-2">
                    <Button
                        variant="outline"
                        onClick={handlePreview}
                        disabled={loadingPreview || sending}
                        className="w-1/4"
                    >
                        {/* 4. Added spinner for the preview button */}
                        {loadingPreview ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Loading...
                            </>
                        ) : (
                            "Preview Email"
                        )}
                    </Button>

                    <Button
                        onClick={confirmAndSendEmail}
                        disabled={sending || loadingPreview}
                        className="w-3/4 bg-[#007cc2] hover:bg-[#007cc2]/60 text-white"
                    >
                        {sending ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Sending Email...
                            </>
                        ) : (
                            <>
                                <Send className="mr-2 h-4 w-4" />
                                Send Notification
                            </>
                        )}
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}

export default EmailForm;