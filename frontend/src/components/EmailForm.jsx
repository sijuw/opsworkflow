import { useEffect, useState } from "react";

import InstitutionSelect from "./InstitutionSelect";
import ResponseCodeSelect from "./ResponseCodeSelect";
import AttachSamplesCheckbox from "./AttachSamplesCheckbox";
import CommentsBox from "./CommentsBox";

import {
    getInstitutions,
    getResponseCodes,
    sendEmail,
} from "../services/api";

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
        const response = await getInstitutions();
        setInstitutions(response.data);
    }

    async function loadResponseCodes() {
        const response = await getResponseCodes();
        setResponseCodes(response.data);
    }

    async function handleSendEmail() {

        try {

            setSending(true);

            await sendEmail({
                institution_id: Number(institution),
                response_code: responseCode || null,
                attach_samples: attachSamples,
                comments: comments,
            });

            alert("Email sent successfully!");

        } catch (error) {

            console.error(error);

            alert("Failed to send email.");

        } finally {

            setSending(false);

        }

    }

    return (
        <>
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
                {sending ? "Sending..." : "Send Email"}
            </button>
        </>
    );
}

export default EmailForm;