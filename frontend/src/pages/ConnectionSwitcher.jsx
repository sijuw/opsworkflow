import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowLeft,
  History,
  Network,
  RefreshCw,
  Settings,
} from "lucide-react";

import PageContainer from "@/components/layout/PageContainer";
import ConnectionSettingsModal from "@/components/ConnectionSettingsModal";
import ConnectionSwitchConfirmDialog from "@/components/ConnectionSwitchConfirmDialog";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

import {
  executeConnectionSwitch,
  getConnectionConfigs,
  getConnectionHistory,
  getConnectionStatus,
  previewConnectionSwitch,
  connectionErrorMessage,
} from "@/services/connectionService";

const ROUTE_STYLES = {
  PRIMARY: {
    dot: "bg-green-500",
    text: "text-green-700 dark:text-green-400",
    chip: "bg-green-100 dark:bg-green-500/10",
  },
  SECONDARY: {
    dot: "bg-amber-500",
    text: "text-amber-700 dark:text-amber-400",
    chip: "bg-amber-100 dark:bg-amber-500/10",
  },
  UNKNOWN: {
    dot: "bg-red-500",
    text: "text-red-700 dark:text-red-400",
    chip: "bg-red-100 dark:bg-red-500/10",
  },
};

function ConnectionSwitcher() {
  const [configs, setConfigs] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);

  const [loadingStatus, setLoadingStatus] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [preview, setPreview] = useState(null);
  const [switching, setSwitching] = useState(false);

  // Fetchers return data rather than setting state, so callers decide what
  // to apply. Effects below guard with a cancelled flag: without it, quickly
  // changing institution could let a slow earlier response land after a later one
  // and show the wrong institution's status.
  const loadConfigs = useCallback(async () => {
    try {
      const { data } = await getConnectionConfigs();
      setConfigs(data);
      return data;
    } catch (error) {
      toast.error(connectionErrorMessage(error, "Could not load connection configurations."));
      return [];
    }
  }, []);

  const refreshStatus = useCallback(async (configId) => {
    if (!configId) return;
    setLoadingStatus(true);
    try {
      const { data } = await getConnectionStatus(configId);
      setStatus(data);
    } catch (error) {
      setStatus(null);
      toast.error(connectionErrorMessage(error, "Could not read live status."));
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  const refreshHistory = useCallback(async (configId) => {
    if (!configId) return;
    try {
      const { data } = await getConnectionHistory(configId);
      setHistory(data);
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const { data } = await getConnectionConfigs();
        if (!cancelled) setConfigs(data);
      } catch (error) {
        if (!cancelled) {
          toast.error(
            connectionErrorMessage(error, "Could not load connection configurations."),
          );
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    // Clearing on deselect is handled where the selection is cleared, so
    // this effect only ever fetches.
    if (!selectedId) return;

    let cancelled = false;

    (async () => {
      setLoadingStatus(true);
      try {
        const [statusRes, historyRes] = await Promise.all([
          getConnectionStatus(selectedId),
          getConnectionHistory(selectedId).catch(() => ({ data: [] })),
        ]);
        if (cancelled) return;
        setStatus(statusRes.data);
        setHistory(historyRes.data);
      } catch (error) {
        if (cancelled) return;
        setStatus(null);
        toast.error(connectionErrorMessage(error, "Could not read live status."));
      } finally {
        if (!cancelled) setLoadingStatus(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  // The route that isn't currently live.
  const targetRoute =
    status?.active_route === "PRIMARY" ? "SECONDARY" : "PRIMARY";

  async function handlePreview() {
    try {
      const { data } = await previewConnectionSwitch({
        config_id: Number(selectedId),
        target_route: targetRoute,
      });
      setPreview(data);
      setConfirmOpen(true);
    } catch (error) {
      toast.error(connectionErrorMessage(error, "Could not prepare the switch."));
    }
  }

  async function handleConfirm() {
    try {
      setSwitching(true);
      const { data } = await executeConnectionSwitch({
        config_id: Number(selectedId),
        target_route: preview.to_route,
        // Guards against another engineer switching between our preview
        // and our write.
        expected_from_route: preview.from_route,
      });

      if (data.confirmed) {
        toast.success(data.message);
      } else {
        toast.warning(data.message);
      }

      setConfirmOpen(false);
      setPreview(null);
      await refreshStatus(selectedId);
      await refreshHistory(selectedId);
    } catch (error) {
      toast.error(connectionErrorMessage(error, "Switch failed."));
    } finally {
      setSwitching(false);
    }
  }

  const routeStyle = ROUTE_STYLES[status?.active_route] ?? ROUTE_STYLES.UNKNOWN;

  return (
    <PageContainer maxWidth="4xl">
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to SRE Dashboard
        </Link>
      </div>

      <Card className="rounded-2xl border border-slate-200 shadow-xl dark:border-slate-800">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#007cc2]/10 text-[#007cc2] dark:bg-[#007cc2]/20 dark:text-[#3399ff]">
                <Network className="h-6 w-6" />
              </div>
              <div className="flex flex-col">
                <CardTitle className="text-2xl">Switch Institution Connection</CardTitle>
                <p className="text-sm font-normal text-slate-500 dark:text-slate-400">
                  Move a partner institution between its provisioned connection routes.
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="icon"
              onClick={() => setSettingsOpen(true)}
              title="Connection switch settings"
              className="shrink-0 dark:border-slate-700"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pt-4">
          <div className="flex flex-col space-y-2">
            <Label htmlFor="connection-institution">Institution</Label>
            <Select value={selectedId} onValueChange={setSelectedId}>
              <SelectTrigger id="connection-institution" className="w-full">
                <SelectValue
                  placeholder={
                    configs.length
                      ? "Select an institution"
                      : "No institutions configured — open settings"
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {configs.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.institution_name} · #{c.interchange_id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Live status */}
          {selectedId && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900/50">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-semibold dark:text-slate-100">
                  Live status
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => refreshStatus(selectedId)}
                  disabled={loadingStatus}
                  className="h-7 text-xs"
                >
                  <RefreshCw
                    className={`mr-1 h-3 w-3 ${loadingStatus ? "animate-spin" : ""}`}
                  />
                  Refresh
                </Button>
              </div>

              {loadingStatus && !status ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Reading from Cosmos...
                </p>
              ) : status ? (
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 font-medium ${routeStyle.chip} ${routeStyle.text}`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${routeStyle.dot}`}
                      />
                      {status.active_medium_label ?? status.active_route}
                    </span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">
                      {status.current_summary}
                    </span>
                    <span className="text-xs text-slate-400 dark:text-slate-500">
                      {status.active_route}
                    </span>
                  </div>

                  <div className="grid gap-1 text-xs text-slate-500 dark:text-slate-400 sm:grid-cols-2">
                    <p>
                      Type:{" "}
                      <span className="font-mono">{status.interchange_type}</span>
                    </p>
                    <p>
                      Cosmos reports:{" "}
                      <span
                        className={
                          status.running
                            ? "text-green-700 dark:text-green-400"
                            : "text-slate-600 dark:text-slate-300"
                        }
                      >
                        {status.running ? "running" : "not running"}
                      </span>
                    </p>
                  </div>

                  {status.note && (
                    <div className="flex items-start gap-2 rounded-md bg-amber-50 p-3 text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      <span>{status.note}</span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Status unavailable.
                </p>
              )}
            </div>
          )}

          {/* Switch action */}
          {status && (
            <Button
              onClick={handlePreview}
              disabled={!status.switchable || switching}
              className="w-full bg-[#007cc2] text-white hover:bg-[#007cc2]/80 disabled:opacity-50"
            >
              <Network className="mr-2 h-4 w-4" />
              {status.switchable
                ? `Switch to ${
                    targetRoute === "PRIMARY"
                      ? status.primary.medium_label
                      : status.secondary.medium_label
                  } (${targetRoute})`
                : "Cannot switch — resolve UNKNOWN route first"}
            </Button>
          )}

          {/* Audit trail */}
          {history.length > 0 && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium text-slate-500 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-400">
                <History className="h-3.5 w-3.5" />
                Recent switches
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-900">
                {history.slice(0, 5).map((h) => (
                  <div
                    key={h.id}
                    className="flex items-center justify-between gap-3 px-4 py-2 text-xs"
                  >
                    <span className="min-w-0 truncate text-slate-600 dark:text-slate-300">
                      <span className="font-medium">
                        {h.from_medium ?? h.from_route} → {h.to_medium ?? h.to_route}
                      </span>
                      <span className="ml-2 font-mono text-slate-400">
                        {h.from_value} → {h.to_value}
                      </span>
                    </span>
                    <span className="flex items-center gap-3">
                      <span
                        className={
                          h.outcome === "SUCCESS"
                            ? "text-green-700 dark:text-green-400"
                            : h.outcome === "FAILED"
                              ? "text-red-700 dark:text-red-400"
                              : "text-amber-700 dark:text-amber-400"
                        }
                      >
                        {h.outcome}
                      </span>
                      <span className="text-slate-400">
                        {new Date(h.created_at).toLocaleString()}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <ConnectionSettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        configs={configs}
        onChanged={async () => {
          const fresh = await loadConfigs();
          // If the selected institution was deleted, clear the stale status panel.
          if (selectedId && !fresh.some((c) => String(c.id) === selectedId)) {
            setSelectedId("");
            setStatus(null);
            setHistory([]);
          } else if (selectedId) {
            refreshStatus(selectedId);
          }
        }}
      />

      <ConnectionSwitchConfirmDialog
        open={confirmOpen}
        onOpenChange={(open) => {
          setConfirmOpen(open);
          if (!open) setPreview(null);
        }}
        preview={preview}
        onConfirm={handleConfirm}
        switching={switching}
      />
    </PageContainer>
  );
}

export default ConnectionSwitcher;
