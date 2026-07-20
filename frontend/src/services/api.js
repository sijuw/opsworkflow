import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export const getInstitutions = () =>
  api.get("/institutions");

export const getResponseCodes = () =>
  api.get("/response-codes");

export const sendEmail = (payload) =>
  api.post("/email/send", payload);

export const previewEmail = (payload) =>
  api.post("/email/preview", payload);

export default api;