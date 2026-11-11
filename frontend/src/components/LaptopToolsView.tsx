import React, { useState, useEffect } from 'react';
import { Terminal, HardDrive, Cpu, Folder, Play, RefreshCw, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { getApiUrl } from '../config/api';

export const LaptopToolsView: React.FC = () => {
  const [vitals, setVitals] = useState<any>(null);
  const [loadingVitals, setLoadingVitals] = useState(false);

  // Command runner state
  const [command, setCommand] = useState('');
  const [commandOutput, setCommandOutput] = useState('');
  const [runningCmd, setRunningCmd] = useState(false);

  // App launcher state
  const [launchMessage, setLaunchMessage] = useState('');

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

  useEffect(() => {
    fetchVitals();
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

  const handleLaunchApp = async (target: string) => {
    try {
      setLaunchMessage(`Launching ${target}...`);
      const res = await fetch(getApiUrl('/api/system/open'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target }),
      });
      const data = await res.json();
      if (data.success) {
        setLaunchMessage(`✔ Launched ${target}`);
      } else {
        setLaunchMessage(`✖ ${data.error || 'Failed to open'}`);
      }
      setTimeout(() => setLaunchMessage(''), 4000);
    } catch (err) {
      setLaunchMessage(`✖ Error: ${err}`);
      setTimeout(() => setLaunchMessage(''), 4000);
    }
  };

  return (
    <div className="flex-1 p-6 sm:p-8 overflow-y-auto space-y-6">
      <div>
        <h2 className="text-xl font-black tracking-widest font-['Orbitron'] text-[#f4f4f6]">
          LAPTOP SYSTEM CONTROL & TOOLS
        </h2>
        <p className="text-xs text-[#f4f4f6]/50 mt-1">
          Full autonomous system access — execute commands, browse files, and inspect machine vitals just like Antigravity.
        </p>
      </div>

      {/* Grid: System Vitals & Quick Launch */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Machine Vitals Panel */}
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
                <span className="text-[#f4f4f6]/40 text-[10px] block">LOGGED IN HOST</span>
                <span className="text-[#00ff66] font-semibold truncate block">{vitals.user} ({vitals.hostname})</span>
              </div>
              {vitals.disk && (
                <div className="bg-[#0a0a0c] p-2.5 border border-[#f4f4f6]/10 col-span-2">
                  <div className="flex justify-between text-[10px] text-[#f4f4f6]/40 mb-1">
                    <span>STORAGE DRIVE</span>
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
              {loadingVitals ? 'Probing host machine...' : 'Vitals unavailable. Ensure backend server is connected.'}
            </p>
          )}
        </div>

        {/* Quick Application Launcher */}
        <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded">
          <div className="flex items-center gap-2 mb-4">
            <Play size={16} className="text-[#00ff66]" />
            <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
              Quick Application Launcher
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {[
              { label: 'Notepad', target: 'notepad.exe' },
              { label: 'Calculator', target: 'calc.exe' },
              { label: 'File Explorer', target: '.' },
              { label: 'PowerShell', target: 'powershell.exe' },
              { label: 'Task Manager', target: 'taskmgr.exe' },
              { label: 'Google Chrome', target: 'chrome.exe' },
            ].map((app) => (
              <button
                key={app.label}
                onClick={() => handleLaunchApp(app.target)}
                className="p-2.5 bg-[#0a0a0c] border border-[#f4f4f6]/10 hover:border-[#00ff66]/50 hover:bg-[#00ff66]/5 text-xs text-left font-mono transition-all flex items-center justify-between group"
              >
                <span className="text-[#f4f4f6]/80 group-hover:text-[#00ff66]">{app.label}</span>
                <Play size={10} className="text-[#f4f4f6]/30 group-hover:text-[#00ff66]" />
              </button>
            ))}
          </div>

          {launchMessage && (
            <div className="mt-3 text-[11px] font-mono text-[#00ff66] bg-[#00ff66]/10 p-2 border border-[#00ff66]/20">
              {launchMessage}
            </div>
          )}
        </div>
      </div>

      {/* Terminal Command Runner */}
      <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded space-y-3">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-[#00ff66]" />
          <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
            Host Terminal & PowerShell Console
          </span>
        </div>
        <p className="text-[11px] text-[#f4f4f6]/40 font-mono">
          Run any command directly on your laptop (e.g., <code>dir</code>, <code>git status</code>, <code>ipconfig</code>, <code>python --version</code>).
        </p>

        <div className="flex gap-2">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRunCommand()}
            placeholder="Enter shell or PowerShell command (e.g. dir, Get-Process)..."
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

        {/* Command Output Terminal Box */}
        {commandOutput && (
          <div className="mt-3 bg-[#050507] border border-[#f4f4f6]/15 p-3 rounded text-xs font-mono text-[#00ff66] max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {commandOutput}
          </div>
        )}
      </div>

      {/* Active Capabilities Checklist */}
      <div className="bg-[#111214] border border-[#f4f4f6]/10 p-5 rounded">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle2 size={16} className="text-[#00ff66]" />
          <span className="text-xs font-bold font-['Orbitron'] uppercase tracking-wider">
            Symbiote Autonomous Access Status
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs font-mono">
          {[
            { name: 'Laptop File Upload & Ingestion', desc: 'Ingests documents, code, images' },
            { name: 'PowerShell / Terminal Execution', desc: 'Direct shell execution on laptop' },
            { name: 'Local File System Read & Write', desc: 'Reads & creates files on host drive' },
            { name: 'Application & Window Launcher', desc: 'Opens software & desktop windows' },
            { name: 'Continuous Microphone Voice Wake', desc: 'Summons Venom via "Venom" wake word' },
            { name: 'ElevenLabs Symbiote Vocalizer', desc: 'Visceral voice synthesis cgSgspJ2...' },
          ].map((cap) => (
            <div key={cap.name} className="p-3 bg-[#0a0a0c] border border-[#f4f4f6]/10">
              <div className="text-[#00ff66] font-semibold text-[11px]">{cap.name}</div>
              <div className="text-[10px] text-[#f4f4f6]/40 mt-0.5">{cap.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
