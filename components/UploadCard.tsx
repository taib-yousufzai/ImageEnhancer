'use client';

import { useState, useEffect } from 'react';
import { startBatchEnhancement, getTaskStatus } from '@/lib/api';
import { validateFile } from '@/lib/validation';

type OutputFormat = 'webp' | 'jpeg' | 'png';

interface TaskState {
  file: File;
  previewUrl: string;
  progress: number;
  message: string;
  status: 'idle' | 'processing' | 'completed' | 'failed';
  resultUrl?: string;
  error?: string;
  estimatedTimeRemaining?: number | null;
}

const PRESETS = [
  { name: '4K UHD', width: 3840, height: 2160 },
  { name: 'Full HD', width: 1920, height: 1080 },
  { name: 'Instagram Portrait', width: 1080, height: 1350 },
  { name: 'Instagram Square', width: 1080, height: 1080 },
  { name: 'Blog Post', width: 1200, height: 630 },
];

export default function UploadCard() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [tasks, setTasks] = useState<Record<string, TaskState>>({});
  const [isDragging, setIsDragging] = useState(false);
  const [isStartingBatch, setIsStartingBatch] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Settings
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('webp');
  const [scale, setScale] = useState<number>(2);
  const [useCustomSize, setUseCustomSize] = useState(false);
  const [customWidth, setCustomWidth] = useState<string>('');
  const [customHeight, setCustomHeight] = useState<string>('');
  const [ultraMode, setUltraMode] = useState(false);

  // Countdown timer for individual tasks
  useEffect(() => {
    const timer = setInterval(() => {
      setTasks(prev => {
        let changed = false;
        const next = { ...prev };

        Object.keys(next).forEach(id => {
          const task = next[id];
          if (task.status === 'processing' && task.estimatedTimeRemaining && task.estimatedTimeRemaining > 0) {
            next[id] = {
              ...task,
              estimatedTimeRemaining: Math.max(0, task.estimatedTimeRemaining - 1)
            };
            changed = true;
          }
        });

        return changed ? next : prev;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFiles = (files: File[]) => {
    const validFiles: File[] = [];
    const newTasks: Record<string, TaskState> = { ...tasks };

    files.forEach(file => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }

      const tempId = `idle-${Math.random().toString(36).substr(2, 9)}`;
      const objectUrl = URL.createObjectURL(file);

      validFiles.push(file);
      newTasks[tempId] = {
        file,
        previewUrl: objectUrl,
        progress: 0,
        message: 'Ready',
        status: 'idle'
      };
    });

    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
      setTasks(newTasks);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(Array.from(e.dataTransfer.files));
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  // Poll Task helper
  const pollTask = async (taskId: string) => {
    let errorCount = 0;
    const interval = setInterval(async () => {
      try {
        const statusData = await getTaskStatus(taskId);
        errorCount = 0;

        setTasks(prev => {
          if (!prev[taskId]) return prev;
          return {
            ...prev,
            [taskId]: {
              ...prev[taskId],
              status: statusData.status as any,
              progress: statusData.progress,
              message: statusData.message,
              estimatedTimeRemaining: statusData.estimated_time_remaining,
              resultUrl: statusData.status === 'completed' ? `${process.env.NEXT_PUBLIC_API_URL}/result/${taskId}` : prev[taskId].resultUrl,
              error: statusData.error
            }
          };
        });

        if (statusData.status === 'completed' || statusData.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        errorCount++;
        if (errorCount > 20) {
          clearInterval(interval);
          setTasks(prev => ({
            ...prev,
            [taskId]: { ...prev[taskId], status: 'failed', error: 'Connection lost' }
          }));
        }
      }
    }, 2000);
  };

  const handleEnhance = async () => {
    const idleTaskEntries = Object.entries(tasks).filter(([_, t]) => t.status === 'idle');
    if (idleTaskEntries.length === 0) return;

    setIsStartingBatch(true);
    setError(null);

    try {
      const filesToUpload = idleTaskEntries.map(([_, t]) => t.file);
      const data = await startBatchEnhancement(
        filesToUpload,
        outputFormat,
        scale,
        useCustomSize ? parseInt(customWidth) || undefined : undefined,
        useCustomSize ? parseInt(customHeight) || undefined : undefined,
        ultraMode
      );

      // Collect successfully started task IDs to poll
      const taskIdsToPoll: string[] = [];

      setTasks(prev => {
        const nextTasks = { ...prev };
        const matchedTempIds = new Set<string>();

        // 1. Match successful tasks
        (data.tasks || []).forEach((tInfo: { filename: string, task_id: string }) => {
          const entry = idleTaskEntries.find(([tempId, task]) =>
            !matchedTempIds.has(tempId) && task.file.name === tInfo.filename
          );
          if (entry) {
            const [tempId, task] = entry;
            matchedTempIds.add(tempId);
            delete nextTasks[tempId];
            nextTasks[tInfo.task_id] = {
              ...task,
              status: 'processing',
              message: 'Queued'
            };
            taskIdsToPoll.push(tInfo.task_id);
          }
        });

        // 2. Match errors
        (data.errors || []).forEach((eInfo: { filename: string, error: string }) => {
          const entry = idleTaskEntries.find(([tempId, task]) =>
            !matchedTempIds.has(tempId) && task.file.name === eInfo.filename
          );
          if (entry) {
            const [tempId, task] = entry;
            matchedTempIds.add(tempId);
            nextTasks[tempId] = {
              ...task,
              status: 'failed',
              error: eInfo.error
            };
          }
        });

        // 3. Fallback for any leftovers
        idleTaskEntries.forEach(([tempId, task]) => {
          if (!matchedTempIds.has(tempId)) {
            nextTasks[tempId] = { ...task, status: 'failed', error: 'Server skipped this image' };
          }
        });

        return nextTasks;
      });

      // Start polling OUTSIDE of state setter
      taskIdsToPoll.forEach(id => pollTask(id));

    } catch (err: any) {
      setError(err.message || 'Failed to start batch');
    } finally {
      setIsStartingBatch(false);
    }
  };

  const handleDownload = (resultUrl: string, originalName: string) => {
    const extension = outputFormat === 'jpeg' ? 'jpg' : outputFormat;
    const nameWithoutExt = originalName.split('.').slice(0, -1).join('.');
    const anchor = document.createElement('a');
    anchor.href = resultUrl;
    anchor.download = `${nameWithoutExt}_enhanced.${extension}`;
    anchor.click();
    anchor.remove();
  };

  const handleBatchDownload = async () => {
    try {
      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();
      const completedTasks = Object.values(tasks).filter(t => t.status === 'completed' && t.resultUrl);
      if (completedTasks.length === 0) return;

      for (const task of completedTasks) {
        try {
          const response = await fetch(task.resultUrl!);
          const blob = await response.blob();
          const extension = outputFormat === 'jpeg' ? 'jpg' : outputFormat;
          const nameWithoutExt = task.file.name.split('.').slice(0, -1).join('.');
          zip.file(`${nameWithoutExt}_enhanced.${extension}`, blob);
        } catch (err) {
          console.error(`Zip fail: ${task.file.name}`, err);
        }
      }

      const content = await zip.generateAsync({ type: 'blob' });
      const anchor = document.createElement('a');
      anchor.href = URL.createObjectURL(content);
      anchor.download = `enhanced_batch_${Date.now()}.zip`;
      anchor.click();
    } catch (err) {
      setError('Failed to create ZIP');
    }
  };

  const hasIdleTasks = Object.values(tasks).some(t => t.status === 'idle');
  const isCurrentlyProcessing = Object.values(tasks).some(t => t.status === 'processing');
  const hasCompletedTasks = Object.values(tasks).some(t => t.status === 'completed');

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900">Batch Enhancer</h2>
        {Object.keys(tasks).length > 0 && !isCurrentlyProcessing && !isStartingBatch && (
          <button
            onClick={() => { setSelectedFiles([]); setTasks({}); setError(null); }}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Clear All
          </button>
        )}
      </div>

      {!isStartingBatch && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${isDragging ? 'border-gray-900 bg-gray-50' : 'border-gray-300 hover:bg-gray-50'}`}
        >
          <input id="file-input" type="file" accept="image/*" multiple onChange={handleFileInputChange} className="hidden" />
          <p className="font-semibold text-gray-900">
            {Object.keys(tasks).length > 0 ? "Add more images to batch" : "Drop images here or click to upload"}
          </p>
        </div>
      )}

      {Object.keys(tasks).length > 0 && (
        <div className="mt-8 space-y-8 animate-fade-in">
          {/* Settings Section (Restored & Fixed UI) */}
          {hasIdleTasks && !isStartingBatch && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-gray-100 pt-8 animate-fade-in overflow-hidden">
              <div className="space-y-6">
                <div>
                  <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] mb-4">Output Format</h3>
                  <div className="flex gap-2 p-1.5 bg-gray-100 rounded-2xl">
                    {['webp', 'jpeg', 'png'].map(fmt => (
                      <button
                        key={fmt}
                        onClick={() => setOutputFormat(fmt as OutputFormat)}
                        className={`flex-1 py-2.5 px-3 text-xs rounded-xl font-bold transition-all ${outputFormat === fmt ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'}`}
                      >
                        {fmt.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-4 bg-indigo-50/50 p-5 rounded-2xl border border-indigo-100/50">
                  <div className="relative flex items-center">
                    <input
                      type="checkbox"
                      id="ultra-mode"
                      checked={ultraMode}
                      onChange={e => setUltraMode(e.target.checked)}
                      className="h-5 w-5 text-indigo-600 border-indigo-200 rounded-lg cursor-pointer focus:ring-offset-0 focus:ring-indigo-500"
                    />
                  </div>
                  <label htmlFor="ultra-mode" className="cursor-pointer select-none">
                    <p className="font-bold text-indigo-950 text-sm">Ultra Quality Mode</p>
                    <p className="text-indigo-600/70 text-[10px] font-medium">Best results with AI denoising.</p>
                  </label>
                </div>
              </div>

              <div className="space-y-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em]">Dimensions</h3>
                  <button onClick={() => setUseCustomSize(!useCustomSize)} className="text-[10px] text-blue-600 hover:text-blue-800 font-bold uppercase tracking-wider">
                    {useCustomSize ? 'Use Presets' : 'Custom Size'}
                  </button>
                </div>

                {!useCustomSize ? (
                  <div className="grid grid-cols-3 gap-3">
                    {[1, 2, 4].map(s => (
                      <button
                        key={s}
                        onClick={() => setScale(s)}
                        className={`py-3.5 rounded-2xl font-black text-sm transition-all border-2 ${scale === s ? 'bg-gray-900 border-gray-900 text-white shadow-lg' : 'bg-white border-gray-100 text-gray-400 hover:border-gray-300'}`}
                      >
                        {s}x
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <select
                      onChange={e => {
                        const p = PRESETS.find(pr => pr.name === e.target.value);
                        if (p) { setCustomWidth(p.width.toString()); setCustomHeight(p.height.toString()); }
                      }}
                      className="w-full py-3.5 px-4 bg-gray-50 border border-gray-200 rounded-2xl text-sm font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    >
                      <option value="" disabled selected>Select Resolution...</option>
                      {PRESETS.map(p => <option key={p.name} value={p.name} className="text-gray-900">{p.name} ({p.width}x{p.height})</option>)}
                    </select>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[10px] font-black text-gray-300 uppercase">W</span>
                        <input
                          type="number"
                          placeholder="0"
                          value={customWidth}
                          onChange={e => setCustomWidth(e.target.value)}
                          className="w-full py-3.5 pl-10 pr-4 bg-gray-50 border border-gray-200 rounded-2xl text-sm font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>
                      <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[10px] font-black text-gray-300 uppercase">H</span>
                        <input
                          type="number"
                          placeholder="0"
                          value={customHeight}
                          onChange={e => setCustomHeight(e.target.value)}
                          className="w-full py-3.5 pl-10 pr-4 bg-gray-50 border border-gray-200 rounded-2xl text-sm font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-4">
            {hasIdleTasks && !isStartingBatch && (
              <button onClick={handleEnhance} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 px-8 rounded-2xl font-bold text-lg shadow-lg shadow-blue-200 transition-all hover:-translate-y-0.5">
                Enhance {Object.values(tasks).filter(t => t.status === 'idle').length} Images
              </button>
            )}
            {hasCompletedTasks && !isCurrentlyProcessing && !isStartingBatch && (
              <button onClick={handleBatchDownload} className="w-full bg-green-600 hover:bg-green-700 text-white py-4 px-8 rounded-2xl font-bold text-lg shadow-lg shadow-green-200 transition-all hover:-translate-y-0.5 flex items-center justify-center gap-2">
                Download All Enhanced (ZIP)
              </button>
            )}
            {isStartingBatch && (
              <div className="w-full bg-blue-50 text-blue-600 py-4 px-8 rounded-2xl font-bold text-center animate-pulse border border-blue-100 flex items-center justify-center gap-3">
                <div className="w-5 h-5 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
                Contacting Server...
              </div>
            )}
          </div>

          <div className="space-y-6">
            <h3 className="text-lg font-bold text-gray-900 border-b border-gray-100 pb-4">Task Gallery</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {Object.entries(tasks).map(([id, task]) => (
                <div key={id} className={`relative group bg-white border ${task.status === 'failed' ? 'border-red-100 bg-red-50/10' : 'border-gray-100'} rounded-2xl p-4 shadow-sm hover:shadow-md transition-all`}>
                  <div className="flex gap-4">
                    <div className="w-24 h-24 flex-shrink-0 bg-gray-100 rounded-xl overflow-hidden border border-gray-100">
                      <img src={task.resultUrl || task.previewUrl} className={`w-full h-full object-cover ${task.status === 'processing' ? 'opacity-50 blur-[1px]' : ''}`} alt="" />
                      {task.status === 'processing' && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                      <p className="text-sm font-bold text-gray-900 truncate">{task.file.name}</p>
                      {task.status === 'idle' && <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 text-gray-500 uppercase tracking-widest mt-1 w-fit">READY</span>}
                      {task.status === 'processing' && (
                        <div className="mt-3 space-y-2">
                          <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
                            <span className="text-gray-400">{task.message}</span>
                            <span className="text-blue-600">{task.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-blue-600 h-full transition-all duration-300" style={{ width: `${task.progress}%` }} />
                          </div>
                          {task.estimatedTimeRemaining ? (
                            <p className="text-[10px] text-blue-500 font-medium animate-pulse">~{Math.round(task.estimatedTimeRemaining)}s left</p>
                          ) : <p className="text-[10px] text-gray-400 italic">Starting...</p>}
                        </div>
                      )}
                      {task.status === 'completed' && (
                        <button onClick={() => handleDownload(task.resultUrl!, task.file.name)} className="mt-3 bg-gray-900 text-white text-[10px] font-bold py-2 px-4 rounded-lg hover:bg-black transition-all active:scale-95 shadow-sm">Download</button>
                      )}
                      {task.status === 'failed' && <div className="mt-1"><p className="text-[10px] text-red-500 font-bold uppercase">Failed</p><p className="text-[10px] text-red-400 line-clamp-2">{task.error}</p></div>}
                    </div>
                  </div>
                  {!isCurrentlyProcessing && !isStartingBatch && (
                    <button onClick={() => setTasks(prev => { const n = { ...prev }; delete n[id]; return n; })} className="absolute top-2 right-2 p-1.5 bg-red-100 text-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-8 p-4 bg-red-50 border-2 border-red-100 rounded-xl text-red-800 text-sm font-bold flex items-center gap-3 animate-fade-in">
          <div className="bg-red-500 text-white rounded-full p-1"><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg></div>
          {error}
        </div>
      )}
    </div>
  );
}
