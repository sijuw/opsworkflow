import { useEffect, useState } from "react";
import { toast } from "sonner"; // Import the toast function

import InstitutionSelect from "./InstitutionSelect";
import ResponseCodeSelect from "./ResponseCodeSelect";
import AttachSamplesCheckbox from "./AttachSamplesCheckbox";
import CommentsBox from "./CommentsBox";
// We removed Notification.jsx and form.css imports
import {
    getInstitutions,
    getResponseCodes,
    sendEmail,
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

    async function handleSendEmail() {
        if (!institution) {
            // Trigger a warning toast
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

            // Trigger a success toast
            toast.success("Email sent successfully!");
            
            // Optional: Clear the form after success
            setComments("");

        } catch (error) {
            console.error(error);
            // Trigger an error toast
            toast.error("Failed to send email. Please try again.");

        } finally {
            setSending(false);
        }
    }

    return (
        <Card className="shadow-xl">
            <CardHeader>
                <CardTitle>
                    📧 Email Notification Portal
                </CardTitle>
                <CardDescription>
                    Notify partner institutions about transaction issues.
                </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6 pt-4">
                {/* The old static Notification component has been removed */}
                
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

                <Button
                    className="w-full mt-4 bg-[#0056b3] hover:bg-[#0056b3]/90 text-white"
                    onClick={handleSendEmail}
                    disabled={sending}
                >
                    {sending ? "Sending Notification..." : "Send Notification"}
                </Button>
            </CardContent>
        </Card>
    );
}

export default EmailForm;