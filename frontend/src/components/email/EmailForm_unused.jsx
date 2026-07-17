import { useEffect, useState } from "react";

import InstitutionSelect from "./InstitutionSelect";
import ResponseCodeSelect from "./ResponseCodeSelect";
import AttachSamplesCheckbox from "./AttachSamplesCheckbox";
import CommentsBox from "./CommentsBox";
import "../styles/form.css";
import Notification from "./Notification";
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


function EmailForm() {

    const [institutions, setInstitutions] = useState([]);
    const [responseCodes, setResponseCodes] = useState([]);
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState("");     

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
        const response = await getInstitutions();
        setInstitutions(response.data);
    }

    async function loadResponseCodes() {
        const response = await getResponseCodes();
        setResponseCodes(response.data);
    }

    

    async function handleSendEmail() {
        if (!institution) {

        setMessageType("error");
        setMessage("Please select an institution.");

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

            setMessageType("success");
            setMessage("Email sent successfully.");

        } catch (error) {

            console.error(error);

            setMessageType("error");
            setMessage("Failed to send email.");

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
            <CardContent>
                <Notification
                    type={messageType}
                    message={message}
                />
                <InstitutionSelect
                institutions={institutions}
                value={institution}
                onChange={setInstitution}
            />

            <br />

            <ResponseCodeSelect
                responseCodes={responseCodes}
                value={responseCode}
                onChange={setResponseCode}
            />

            <br />

            <CommentsBox
                value={comments}
                onChange={setComments}
            />

            <br />

            <AttachSamplesCheckbox
                checked={attachSamples}
                onChange={setAttachSamples}
            />

            <br />

            <button
                onClick={handleSendEmail}
                disabled={sending}
            >
                {sending ? "Sending Notification..." : "Send Notification"}
            </button>
            </CardContent>
        </Card>
        
                
        
    );
}

export default EmailForm;