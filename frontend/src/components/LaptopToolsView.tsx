import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Cpu,
  Folder,
  Play,
  RefreshCw,
  CheckCircle2,
  Search,
  AppWindow,
  XCircle,
  FileText,
} from 'lucide-react';
import { getApiUrl } from '../config/api';

export const LaptopToolsView: React.FC = () => {
  const [vitals, setVitals] = useState<any>(null);
  const [loadingVitals, setLoadingVitals] = useState(false);

  // Command runner state
  const [command, setCommand] = useState('');
  const [commandOutput, setCommandOutput] = useState('');
  const [runningCmd, setRunningCmd] = useState(false);

  // App launcher & Installed Apps state
  const [installedApps, setInstalledApps] = useState<Array<{ name: string; target: string }>>([]);
  const [appFilter, setAppFilter] = useState('');
  const [runningApps, setRunningApps] = useState<any[]>([]);
  const [launchMessage, setLaunchMessage] = useState('');

  // File Search state
  const [fileQuery, setFileQuery] = useState('');
  const [fileResults, setFileResults] = useState<any[]>([]);
  const [searchingFiles, setSearchingFiles] = useState(false);

  const fetchVitals = async () => {
    setLoadingVitals(true);
    try {
      const res = await fetch(getApiUrl('/api/system/vitals'));
      if (res.ok) {
        const data = await res.json();
        setVitals(data.vitals || null);
      }
    } catch (e) {
      console.warn('Vitals probe failed:', e);
    } finally {
      setLoadingVitals(false);
    }
  };

  const fetchApps = async () => {
    try {
      const [instRes, runRes] = await Promise.all([
        fetch(getApiUrl('/api/system/apps/installed')),
        fetch(getApiUrl('/api/system/apps/running')),
      ]);
      if (instRes.ok) {
        const d = await instRes.json();
        setInstalledApps(d.apps || []);
      }
      if (runRes.ok) {
        const r = await runRes.json();
        setRunningApps(r.running_apps || []);
      }
    } catch {}
  };

  useEffect(() => {
    fetchVitals();
    fetchApps();
  }, []);

  const handleRunCommand = async () => {
    if (!command.trim() || runningCmd) return;
    setRunningCmd(true);
    setCommandOutput('Executing on host machine...');
    try {
      const res = await fetch(getApiUrl('/api/system/command'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command.trim() }),
      });
      const data = await res.json();
      if (data.stdout || data.stderr) {
        setCommandOutput(`${data.stdout || ''}${data.stderr ? `\n[STDERR]:\n${data.stderr}` : ''}`);
      } else if (data.error) {
        setCommandOutput(`[ERROR]: ${data.error}`);
      } else {
        setCommandOutput('(Execution completed with no output)');
      }
    } catch (err) {
      setCommandOutput(`Failed to execute: ${err}`);
    } finally {
      setRunningCmd(false);
    }
  };

  const handleLaunchApp = async (target: string, label?: string) => {
    try {
      setLaunchMessage(`Launching ${label || target}...`);
      const res = await fetch(getApiUrl('/api/system/open'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target }),
      });
      const data = await res.json();
      if (data.success) {
        setLaunchMessage(`✔ ${data.message || `Launched ${label || target}`}`);
        setTimeout(fetchApps, 1200);
      } else {
        setLaunchMessage(`✖ ${data.error || 'Failed to open'}`);
      }
      setTimeout(() => setLaunchMessage(''), 4000);
    } catch (err) {
      setLaunchMessage(`✖ Error: ${err}`);
      setTimeout(() => setLaunchMessage(''), 4000);
    }
  };

  const handleCloseApp = async (name: string) => {
    try {
      const res = await fetch(getApiUrl('/api/system/apps/close'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: name }),
      });
      if (res.ok) {
        setLaunchMessage(`✔ Closed ${name}`);
        setTimeout(fetchApps, 800);
      }
    } catch {}
  };

  const handleSearchFiles = async () => {
    if (!fileQuery.trim() || searchingFiles) return;
    setSearchingFiles(true);
    try {
      const res = await fetch(getApiUrl('/api/system/files/search'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: fileQuery.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        setFileResults(data.matches || []);
      }
    } catch {} finally {
      setSearchingFiles(false);
    }
  };

  const filteredApps = installedApps.filter((a) =>
    a.name.toLowerCase().includes(appFilter.toLowerCase())
  );

  return (
    <div className="flex-1 p-6 sm:p-8 overflow-y-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-black tracking-widest font-['Orbitron'] text-[#f4f4f6]">
            DESKTOP CONTROL CENTER
          </h2>
          <p className="text-xs text-[#f4f4f6]/50 mt-1">
            Full access to all files, user directories, terminal shell, and installed Windows applications.
          </p>
        </div>
        {launchMessage && (
          <div className="text-xs font-mono text-[#00ff66] bg-[#00ff66]/10 px-3 py-1.5 border border-[#00ff66]/30 rounded">
            {launchMessage}
          </div>
        )}
      </div>

      {/* Grid 1: Machine Vitals & User Folders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Cpu size={16} className="text-[#00ff66]" />
              <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
                Machine Vitals
              </span>
            </div>
            <button
              onClick={fetchVitals}
              disabled={loadingVitals}
              className="text-[#f4f4f6]/40 hover:text-[#00ff66] transition-colors p-1"
              title="Refresh Vitals"
            >
              <RefreshCw size={13} className={loadingVitals ? 'animate-spin' : ''} />
            </button>
          </div>

          {vitals ? (
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-[#0a0a0c] p-2.5 border border-[#f4f4f6]/10">
                <span className="text-[#f4f4f6]/40 text-[10px] block">OPERATING SYSTEM</span>
                <span className="text-[#f4f4f6] font-semibold truncate block">{vitals.os}</span>
              </div>
              <div className="bg-[#0a0a0c] p-2.5 border border-[#f4f4f6]/10">
                <span className="text-[#f4f4f6]/40 text-[10px] block">HOST MACHINE</span>
                <span className="text-[#00ff66] font-semibold truncate block">{vitals.user} ({vitals.hostname})</span>
              </div>
              {vitals.disk && (
                <div className="bg-[#0a0a0c] p-2.5 border border-[#f4f4f6]/10 col-span-2">
                  <div className="flex justify-between text-[10px] text-[#f4f4f6]/40 mb-1">
                    <span>C: DRIVE STORAGE</span>
                    <span>{vitals.disk.free_gb} GB FREE / {vitals.disk.total_gb} GB</span>
                  </div>
                  <div className="w-full bg-[#1b1c20] h-2 rounded overflow-hidden">
                    <div
                      className="bg-[#00ff66] h-full"
                      style={{ width: `${100 - vitals.disk.percent_free}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-[#f4f4f6]/40 font-mono">
              {loadingVitals ? 'Probing laptop...' : 'Vitals unavailable.'}
            </p>
          )}
        </div>

        {/* User Directories Quick Open */}
        <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded">
          <div className="flex items-center gap-2 mb-4">
            <Folder size={16} className="text-[#00ff66]" />
            <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
              Quick Folder Access
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {['Desktop', 'Downloads', 'Documents', 'OneDrive', 'Pictures', 'Music', 'Videos', 'Home'].map((dir) => (
              <button
                key={dir}
                onClick={() => handleLaunchApp(dir.toLowerCase(), dir)}
                className="p-2.5 bg-[#0a0a0c] border border-[#f4f4f6]/10 hover:border-[#00ff66]/50 hover:bg-[#00ff66]/5 text-xs font-mono text-left flex items-center gap-2 transition-all group"
              >
                <Folder size={12} className="text-[#00ff66]" />
                <span className="text-[#f4f4f6]/80 group-hover:text-[#00ff66] truncate">{dir}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Grid 2: Installed Applications & File Search */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Installed Windows Applications */}
        <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AppWindow size={16} className="text-[#00ff66]" />
              <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
                Installed Applications ({installedApps.length})
              </span>
            </div>
            <button onClick={fetchApps} className="text-[#f4f4f6]/40 hover:text-[#00ff66] p-1">
              <RefreshCw size={12} />
            </button>
          </div>
          <input
            type="text"
            value={appFilter}
            onChange={(e) => setAppFilter(e.target.value)}
            placeholder="Filter installed apps (e.g. Chrome, VS Code, Canva)..."
            className="w-full bg-[#0a0a0c] border border-[#f4f4f6]/15 px-3 py-1.5 text-xs font-mono text-[#f4f4f6] placeholder-[#f4f4f6]/30 mb-3 outline-none focus:border-[#00ff66]"
          />
          <div className="grid grid-cols-2 gap-1.5 max-h-52 overflow-y-auto pr-1">
            {filteredApps.slice(0, 60).map((app, i) => (
              <button
                key={i}
                onClick={() => handleLaunchApp(app.target, app.name)}
                className="p-2 bg-[#0a0a0c] border border-[#f4f4f6]/10 hover:border-[#00ff66]/50 hover:bg-[#00ff66]/5 text-[11px] font-mono text-left flex items-center justify-between group"
                title={app.name}
              >
                <span className="text-[#f4f4f6]/80 group-hover:text-[#00ff66] truncate">{app.name}</span>
                <Play size={10} className="text-[#f4f4f6]/30 group-hover:text-[#00ff66] flex-shrink-0 ml-1" />
              </button>
            ))}
          </div>
        </div>

        {/* Instant Laptop File Search */}
        <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded flex flex-col">
          <div className="flex items-center gap-2 mb-3">
            <Search size={16} className="text-[#00ff66]" />
            <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
              Search All Laptop Files
            </span>
          </div>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={fileQuery}
              onChange={(e) => setFileQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearchFiles()}
              placeholder="Search filename (e.g. resume, .pdf, notes)..."
              className="flex-1 bg-[#0a0a0c] border border-[#f4f4f6]/15 px-3 py-1.5 text-xs font-mono text-[#f4f4f6] placeholder-[#f4f4f6]/30 outline-none focus:border-[#00ff66]"
            />
            <button
              onClick={handleSearchFiles}
              disabled={searchingFiles}
              className="px-3 py-1.5 bg-[#00ff66] text-black font-['Orbitron'] text-[11px] font-bold uppercase"
            >
              {searchingFiles ? '...' : 'FIND'}
            </button>
          </div>
          <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
            {fileResults.length > 0 ? (
              fileResults.map((f, idx) => (
                <button
                  key={idx}
                  onClick={() => handleLaunchApp(f.path, f.name)}
                  className="w-full p-2 bg-[#0a0a0c] border border-[#f4f4f6]/10 hover:border-[#00ff66]/50 text-left flex items-center justify-between group"
                >
                  <div className="min-w-0 pr-2">
                    <div className="text-[11px] font-mono text-[#f4f4f6] group-hover:text-[#00ff66] truncate flex items-center gap-1.5">
                      <FileText size={11} className="text-[#00ff66] flex-shrink-0" />
                      <span className="truncate">{f.name}</span>
                    </div>
                    <div className="text-[9px] font-mono text-[#f4f4f6]/40 truncate">{f.path}</div>
                  </div>
                  <span className="text-[9px] text-[#00ff66] uppercase tracking-wider flex-shrink-0">OPEN</span>
                </button>
              ))
            ) : (
              <p className="text-xs font-mono text-[#f4f4f6]/30 text-center py-8">
                Searches Desktop, Downloads, Documents & OneDrive
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Currently Running Applications */}
      {runningApps.length > 0 && (
        <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 size={16} className="text-[#00ff66]" />
            <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
              Active Running Windows ({runningApps.length})
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {runningApps.map((app, idx) => (
              <div
                key={idx}
                className="p-2.5 bg-[#0a0a0c] border border-[#f4f4f6]/10 flex items-center justify-between text-xs font-mono"
              >
                <div className="min-w-0 pr-2">
                  <div className="text-[#f4f4f6] font-semibold truncate">{app.ProcessName}</div>
                  <div className="text-[10px] text-[#f4f4f6]/40 truncate">{app.MainWindowTitle}</div>
                </div>
                <button
                  onClick={() => handleCloseApp(app.ProcessName)}
                  className="text-red-400/60 hover:text-red-400 p-1 flex-shrink-0"
                  title="Close app"
                >
                  <XCircle size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Terminal Command Runner */}
      <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded space-y-3">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-[#00ff66]" />
          <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
            Host Terminal & PowerShell Console
          </span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRunCommand()}
            placeholder="Enter PowerShell command (e.g. dir, Get-Process, ipconfig)..."
            disabled={runningCmd}
            className="flex-1 bg-[#0a0a0c] border border-[#f4f4f6]/20 px-3 py-2 text-xs font-mono text-[#f4f4f6] placeholder-[#f4f4f6]/30 focus:border-[#00ff66] outline-none"
          />
          <button
            onClick={handleRunCommand}
            disabled={runningCmd || !command.trim()}
            className="px-4 py-2 bg-[#00ff66] text-black font-['Orbitron'] text-xs font-bold tracking-wider uppercase hover:shadow-[0_0_15px_#00ff66] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {runningCmd ? 'RUNNING...' : 'EXECUTE'}
          </button>
        </div>

        {commandOutput && (
          <div className="mt-3 bg-[#050507] border border-[#f4f4f6]/15 p-3 rounded text-xs font-mono text-[#00ff66] max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {commandOutput}
          </div>
        )}
      </div>
    </div>
  );
};
