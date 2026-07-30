import api from "./api";

export const getConnectionConfigs = () => api.get("/connections/configs");

export const createConnectionConfig = (payload) => api.post("/connections/configs", payload);

export const updateConnectionConfig = (id, payload) =>
  api.put(`/connections/configs/${id}`, payload);

export const deleteConnectionConfig = (id) => api.delete(`/connections/configs/${id}`);

export const getConnectionStatus = (configId) => api.get(`/connections/status/${configId}`);

export const previewConnectionSwitch = (payload) =>
  api.post("/connections/switch/preview", payload);

export const executeConnectionSwitch = (payload) => api.post("/connections/switch", payload);

export const getConnectionHistory = (configId) => api.get(`/connections/history/${configId}`);

/**
 * The API returns actionable messages in `detail`; surface those rather than
 * a generic failure, because during an incident the difference between
 * "credentials rejected" and "matches neither route" is the whole diagnosis.
 */
export function connectionErrorMessage(error, fallback = "Request failed.") {
  return error?.response?.data?.detail || error?.message || fallback;
}
