import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Page, Chip } from "../components/layout";

export default function Ops() {
  const [diag, setDiag] = useState<any>(null);
  const [backups, setBackups] = useState<any>(null);
  const [integrity, setIntegrity] = useState<any>(null);
  const [seed, setSeed] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const refresh = () => {
    api.requestDiagnostics().then(setDiag).catch(()=>{});
    api.requestBackups().then(setBackups).catch(()=>{});
    api.requestIntegrity().then(setIntegrity).catch(()=>{});
    api.requestSeedChecksum().then(setSeed).catch(()=>{});
  };

  useEffect(refresh, []);

  const doBackup = async () => {
    setMsg("Creating backup…");
    try {
      const r: any = await api.createBackup();
      setMsg(r.ok ? `Backup created: ${r.file} (${(r.size_bytes/1024).toFixed(1)} KB) integrity ${r.integrity?.result}` : `Backup failed: ${r.error}`);
      refresh();
    } catch (e: any) { setMsg(e.message); }
  };
  const doVacuum = async () => {
    setMsg("Running VACUUM…");
    try { const r:any = await api.vacuum(); setMsg(r.ok?"VACUUM complete - space reclaimed.":"VACUUM failed: "+r.error); refresh(); } catch(e:any){setMsg(e.message);}
  };

  return (
    <Page
      title="Ops - Local Backup, Diagnostics & Maintenance"
      description="SQLite WAL integrity, one-click backups to data/backups/, seed checksum, CPU/memory telemetry. Local only. Personal research software, not investment advice."
      actions={
        <div className="flex gap-2">
          <button onClick={doBackup} className="rounded-chip bg-accent text-bg-0 px-3 py-1.5 text-xs font-semibold">One-Click Backup</button>
          <button onClick={doVacuum} className="rounded-chip border border-border bg-bg-1 px-3 py-1.5 text-xs text-ink-1">VACUUM</button>
          <button onClick={refresh} className="rounded-chip border border-border bg-bg-1 px-3 py-1.5 text-xs text-ink-1">Refresh</button>
        </div>
      }
    >
      {msg && <div role="status" className="rounded-card border border-accent/60 bg-accent-weak px-3 py-2 text-xs font-mono text-ink-0">{msg}</div>}

      <div className="grid lg:grid-cols-3 gap-4">
        <Card title="System Diagnostics" padding="md">
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between"><span className="text-ink-2">CPU</span><span className="text-ink-0">{diag?.cpu_percent != null ? `${diag.cpu_percent.toFixed(1)}%` : "0.00"}</span></div>
            <div className="flex justify-between"><span className="text-ink-2">DB Size</span><span className="text-ink-0">{diag?.db_size_bytes != null ? `${(diag.db_size_bytes/1024/1024).toFixed(2)} MB` : "0.00"}</span></div>
            <div className="flex justify-between"><span className="text-ink-2">DB Path</span><span className="text-ink-1 truncate max-w-[150px]">{diag?.db_path ?? "Not reported in filing"}</span></div>
            <div className="flex justify-between"><span className="text-ink-2">Worker</span><span className="text-pos text-[11px]">{diag?.worker ?? "Not reported in filing"}</span></div>
            <div className="border-t border-border pt-2">
              <span className="text-ink-2 text-[10px] uppercase">Integrity</span>
              <div className="mt-1 flex items-center gap-2"><Chip tone={integrity?.ok ? "positive" : "negative"} size="sm">{integrity?.result ?? "Not reported in filing"}</Chip><span className="text-ink-2 text-[11px]">{integrity?.db ?? ""}</span></div>
            </div>
          </div>
          {/* CPU/memory bars - pure SVG */}
          <svg width={260} height={24} viewBox="0 0 260 24" role="img" aria-label="CPU and DB size bars" className="w-full h-auto mt-3">
            <rect x={0} y={0} width={260} height={8} rx={4} fill="var(--bg-2)" />
            <rect x={0} y={0} width={Math.min(260, (diag?.cpu_percent ?? 0) * 2.6)} height={8} rx={4} fill="var(--accent)" />
            <text x={0} y={20} fontSize={7} fill="var(--ink-2)" fontFamily="IBM Plex Mono">CPU {diag?.cpu_percent ?? "0.0%"}%</text>
          </svg>
        </Card>

        <Card title="Seed Immutability" padding="md">
          <p className="text-xs font-mono text-ink-1">File: {seed?.file ?? "Not reported in filing"}</p>
          <p className="text-xs font-mono text-ink-0 mt-1">SHA256: {seed?.sha256_short ?? seed?.sha256?.slice(0,16) ?? "Not reported in filing"}</p>
          <p className="text-[11px] font-mono text-ink-2 mt-1 break-all">{seed?.sha256 ?? ""}</p>
          <p className="text-[11px] text-ink-2 mt-2">{seed?.note ?? ""}</p>
          <Chip tone={seed?.ok ? "positive" : "negative"} size="sm" className="mt-2">{seed?.ok ? "Checksum verified" : "Not reported in filing"}</Chip>
        </Card>

        <Card title="Backups (data/backups/)" padding="md">
          <p className="text-xs font-mono text-ink-2">{backups?.count ?? 0} snapshot(s) - newest first, max 20</p>
          <ul className="mt-2 space-y-1 text-xs font-mono">
            {(backups?.items ?? []).slice(0, 6).map((b: any) => (
              <li key={b.file} className="flex justify-between border-b border-border/40 py-1">
                <span className="text-ink-0 truncate max-w-[160px]">{b.file}</span>
                <span className="text-ink-2">{(b.size_bytes/1024).toFixed(0)} KB</span>
              </li>
            ))}
            {(backups?.items?.length ?? 0) === 0 && <li className="text-ink-2">No backups yet - click One-Click Backup.</li>}
          </ul>
          <p className="text-[11px] font-mono text-ink-2 mt-2">Backups are timestamped SQLite copies with PRAGMA integrity_check verified; restore via POST /ops/restore/{`{file}`}. Keep data/backups/ on your backup drive for portability (US-0960 cold-standby).</p>
        </Card>
      </div>

      <Card title="Operational Notes" padding="md">
        <ul className="list-disc list-inside text-xs text-ink-1 space-y-1">
          <li>Local Docker only - no cloud, no Postgres, no Redis, no paid APIs; WAL mode with busy_timeout.</li>
          <li>Schedule: run integrity_check weekly and VACUUM monthly (US-0957); practice restore quarterly (US-0995 fire drill).</li>
          <li>Portability: move data/app.db + data/backups/ to a new machine per US-0960/US-0998 procedure.</li>
          <li>Logs: structured logs via docker compose logs --tail=50 api (US-0963) - no elevated privileges needed (US-0976).</li>
        </ul>
      </Card>

      <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Backup/restore and maintenance run locally; no data leaves the machine.</p>
    </Page>
  );
}