import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8001",
});

export const getInstitutions = () => api.get("/institutions");

export default api;

export const getResponseCodes = () =>
    api.get("/response-codes");

export const sendEmail = (payload) =>
    api.post("/email/send", payload);