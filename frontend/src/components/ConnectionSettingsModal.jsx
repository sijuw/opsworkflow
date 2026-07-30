import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Pencil, Plus, Trash2, X } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import {
  createConnectionConfig,
  deleteConnectionConfig,
  updateConnectionConfig,
  connectionErrorMessage,
} from "@/services/connectionService";

// Mirrors STRATEGY_BY_TYPE on the backend. REST switches a single port;
// postbridge types replace a whole connection list.
const INTERCHANGE_TYPES = [
  { value: "rest_interchange", label: "REST interchange", strategy: "REMOTE_URL" },
  {
    value: "bankcashoutpostbridge",
    label: "Bank cashout postbridge",
    strategy: "SINK_CONNECTIONS",
  },
  { value: "uppostbridge", label: "UP postbridge", strategy: "SINK_CONNECTIONS" },
  { value: "postbridge", label: "Postbridge", strategy: "SINK_CONNECTIONS" },
  {
    value: "coralpaypostbridge",
    label: "CoralPay postbridge",
    strategy: "SINK_CONNECTIONS",
  },
];

const strategyFor = (type) =>
  INTERCHANGE_TYPES.find((t) => t.value === type)?.strategy ?? "REMOTE_URL";

// Mirrors MEDIUM_LABELS on the backend. What the route physically runs over —
// required, because the route name alone means different things per
// institution (PRIMARY is GCP VPN for most banks, a leased line for NIBSS).
const MEDIUMS = [
  { value: "VPN_GCP", label: "VPN (GCP)" },
  { value: "VPN_AWS", label: "VPN (AWS)" },
  { value: "LEASED_LINE", label: "Leased line" },
  { value: "OTHER", label: "Other" },
];

const blankForm = () => ({
  id: null,
  institution_name: "",
  interchange_id: "",
  interchange_type: "rest_interchange",
  primary: { medium: "VPN_GCP", medium_note: "", endpoints: [{ host: "", port: "" }] },
  secondary: { medium: "VPN_AWS", medium_note: "", endpoints: [{ host: "", port: "" }] },
});

function RouteEditor({ label, route, needsHost, onChange, allowMultiple }) {
  const rows = route.endpoints;
  const setRows = (next) => onChange({ ...route, endpoints: next });
  const update = (i, field, value) =>
    setRows(rows.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  return (
    <div className="space-y-2">
      <Label>{label}</Label>

      <Select
        value={route.medium}
        onValueChange={(medium) => onChange({ ...route, medium })}
      >
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {MEDIUMS.map((m) => (
            <SelectItem key={m.value} value={m.value}>
              {m.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Input
        placeholder="Note (optional) — e.g. tunnel B, reprovisioned May 2026"
        value={route.medium_note ?? ""}
        onChange={(e) => onChange({ ...route, medium_note: e.target.value })}
        className="text-xs"
      />

      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Connections
        </span>
        {allowMultiple && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setRows([...rows, { host: "", port: "" }])}
            className="h-7 text-xs"
          >
            <Plus className="mr-1 h-3 w-3" />
            Add connection
          </Button>
        )}
      </div>

      {rows.map((row, i) => (
        <div key={i} className="flex items-center gap-2">
          {needsHost && (
            <Input
              placeholder="Host / IP"
              value={row.host ?? ""}
              onChange={(e) => update(i, "host", e.target.value)}
              className="flex-1"
            />
          )}
          <Input
            placeholder="Port"
            inputMode="numeric"
            value={row.port ?? ""}
            onChange={(e) => update(i, "port", e.target.value)}
            className={needsHost ? "w-28" : "flex-1"}
          />
          {allowMultiple && rows.length > 1 && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => setRows(rows.filter((_, idx) => idx !== i))}
              className="h-9 w-9 shrink-0 text-slate-400 hover:text-red-600"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}

function ConnectionSettingsModal({ open, onOpenChange, configs, onChanged }) {
  const [form, setForm] = useState(blankForm());
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);

  // Reset on close is done here rather than in an effect, so state changes
  // stay tied to the event that caused them.
  function handleOpenChange(next) {
    if (!next) {
      setForm(blankForm());
      setEditing(false);
    }
    onOpenChange(next);
  }

  const strategy = strategyFor(form.interchange_type);
  const needsHost = strategy === "SINK_CONNECTIONS";
  const allowMultiple = strategy === "SINK_CONNECTIONS";

  function startEdit(config) {
    setEditing(true);
    setForm({
      id: config.id,
      institution_name: config.institution_name,
      interchange_id: String(config.interchange_id),
      interchange_type: config.interchange_type,
      primary: {
        medium: config.primary.medium,
        medium_note: config.primary.medium_note ?? "",
        endpoints: config.primary.endpoints.map((e) => ({
          host: e.host ?? "",
          port: String(e.port),
        })),
      },
      secondary: {
        medium: config.secondary.medium,
        medium_note: config.secondary.medium_note ?? "",
        endpoints: config.secondary.endpoints.map((e) => ({
          host: e.host ?? "",
          port: String(e.port),
        })),
      },
    });
  }

  function toEndpoints(rows) {
    return rows
      .filter((r) => String(r.port).trim() !== "")
      .map((r) => ({
        host: needsHost ? r.host.trim() : null,
        port: Number(r.port),
      }));
  }

  async function handleSave() {
    const primary = toEndpoints(form.primary.endpoints);
    const secondary = toEndpoints(form.secondary.endpoints);

    if (!form.institution_name.trim()) return toast.warning("Institution name is required.");
    if (!String(form.interchange_id).trim())
      return toast.warning("Interchange ID is required.");
    if (!primary.length || !secondary.length)
      return toast.warning("Both routes need at least one connection.");

    // Checked here as well as server-side so the reason is immediate: a
    // pool must keep its size across a switch.
    if (allowMultiple && primary.length !== secondary.length) {
      return toast.warning(
        `Route sizes differ (${primary.length} vs ${secondary.length}). A connection pool must keep the same number of connections.`,
      );
    }

    const payload = {
      institution_name: form.institution_name.trim(),
      interchange_type: form.interchange_type,
      primary: {
        medium: form.primary.medium,
        medium_note: form.primary.medium_note?.trim() || null,
        endpoints: primary,
      },
      secondary: {
        medium: form.secondary.medium,
        medium_note: form.secondary.medium_note?.trim() || null,
        endpoints: secondary,
      },
    };

    try {
      setSaving(true);
      if (form.id) {
        await updateConnectionConfig(form.id, payload);
        toast.success(`${payload.institution_name} updated.`);
      } else {
        await createConnectionConfig({
          ...payload,
          interchange_id: Number(form.interchange_id),
        });
        toast.success(`${payload.institution_name} added.`);
      }
      setForm(blankForm());
      setEditing(false);
      onChanged?.();
    } catch (error) {
      toast.error(connectionErrorMessage(error, "Could not save configuration."));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(config) {
    try {
      await deleteConnectionConfig(config.id);
      toast.success(`${config.institution_name} removed.`);
      if (form.id === config.id) {
        setForm(blankForm());
        setEditing(false);
      }
      onChanged?.();
    } catch (error) {
      toast.error(connectionErrorMessage(error, "Could not delete configuration."));
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Connection switch settings</DialogTitle>
          <DialogDescription>
            Register the two candidate routes for each institution. OpsFlow stores
            only these; Cosmos remains the source of truth.
          </DialogDescription>
        </DialogHeader>

        {/* Existing configs */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium text-slate-500 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-400">
            Configured institutions ({configs.length})
          </div>

          {configs.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-slate-500 dark:text-slate-400">
              Nothing configured yet.
            </p>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-900">
              {configs.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between gap-3 px-4 py-3 text-sm"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-slate-900 dark:text-slate-100">
                      {c.institution_name}
                      <span className="ml-2 text-xs font-normal text-slate-500 dark:text-slate-400">
                        #{c.interchange_id} · {c.interchange_type}
                      </span>
                    </p>
                    <p className="mt-0.5 truncate font-mono text-xs text-slate-500 dark:text-slate-400">
                      {c.primary.medium_label}:{" "}
                      {c.primary.endpoints
                        .map((e) => (e.host ? `${e.host}:${e.port}` : e.port))
                        .join(", ")}
                      {"  ↔  "}
                      {c.secondary.medium_label}:{" "}
                      {c.secondary.endpoints
                        .map((e) => (e.host ? `${e.host}:${e.port}` : e.port))
                        .join(", ")}
                    </p>
                  </div>

                  <div className="flex shrink-0 gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => startEdit(c)}
                      className="h-8 w-8"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(c)}
                      className="h-8 w-8 text-slate-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add / edit form */}
        <div className="space-y-4 rounded-xl border border-slate-200 p-4 dark:border-slate-800">
          <h4 className="text-sm font-semibold dark:text-slate-100">
            {editing ? `Edit ${form.institution_name || "institution"}` : "Add an institution"}
          </h4>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="connection-institution-name">Institution name</Label>
              <Input
                id="connection-institution-name"
                value={form.institution_name}
                onChange={(e) => setForm({ ...form, institution_name: e.target.value })}
                placeholder="ZENITH ATS"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="connection-interchange-id">Interchange ID</Label>
              <Input
                id="connection-interchange-id"
                inputMode="numeric"
                value={form.interchange_id}
                disabled={editing}
                onChange={(e) =>
                  setForm({ ...form, interchange_id: e.target.value })
                }
                placeholder="28"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="connection-type">Interchange type</Label>
            <Select
              value={form.interchange_type}
              onValueChange={(value) => {
                const nextStrategy = strategyFor(value);
                // Collapse to a single connection when moving to REST,
                // which switches only a port.
                setForm((f) => ({
                  ...f,
                  interchange_type: value,
                  primary:
                    nextStrategy === "REMOTE_URL"
                      ? { ...f.primary, endpoints: f.primary.endpoints.slice(0, 1) }
                      : f.primary,
                  secondary:
                    nextStrategy === "REMOTE_URL"
                      ? { ...f.secondary, endpoints: f.secondary.endpoints.slice(0, 1) }
                      : f.secondary,
                }));
              }}
            >
              <SelectTrigger id="connection-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INTERCHANGE_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {needsHost
                ? "Replaces the whole connection list — both host and port."
                : "Switches only the port inside remoteUrl; the host is preserved."}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <RouteEditor
              label="Primary route"
              route={form.primary}
              needsHost={needsHost}
              allowMultiple={allowMultiple}
              onChange={(primary) => setForm({ ...form, primary })}
            />
            <RouteEditor
              label="Secondary route"
              route={form.secondary}
              needsHost={needsHost}
              allowMultiple={allowMultiple}
              onChange={(secondary) => setForm({ ...form, secondary })}
            />
          </div>
        </div>

        <DialogFooter>
          {editing && (
            <Button
              variant="outline"
              onClick={() => {
                setForm(blankForm());
                setEditing(false);
              }}
              disabled={saving}
              className="dark:border-slate-700 dark:text-slate-300"
            >
              Cancel edit
            </Button>
          )}

          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-[#007cc2] text-white hover:bg-[#0056b3]/80"
          >
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : editing ? (
              "Save changes"
            ) : (
              "Add bank"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ConnectionSettingsModal;
