import axios from "axios";

// Always via the /api proxy — nginx (prod) and vite (dev) attach the
// Authorization header there, so no token is ever bundled into the client.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
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