import React, { useCallback, useState, useEffect } from 'react';
import { useBlocker } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  UploadCloud, FileText, Loader2, CheckCircle, AlertCircle,
  RotateCcw, Check, X, Clock, Cpu, Database, Zap, RefreshCw, FileSearch, Brain
} from 'lucide-react';
import toast from 'react-hot-toast';
import { uploadInvoiceStreaming, saveInvoice } from '../services/api';
import ExtractedDataDisplay from '../components/ExtractedDataDisplay';

// --- Step definitions ---
type StepId =
  | 'reading'
  | 'sending_to_ai'
  | 'waiting_for_ai'
  | 'ai_failed'
  | 'trying_new_ai'
  | 'ai_answering'
  | 'preparing_data'
  | 'saving_data';

type StepStatus = 'pending' | 'active' | 'done' | 'error' | 'hidden';

interface Step {
  id: StepId;
  label: string;
  icon: React.ReactNode;
  status: StepStatus;
}

const makeSteps = (): Step[] => [
  { id: 'reading',        label: 'Reading Invoice',      icon: <FileSearch size={14} />, status: 'pending' },
  { id: 'sending_to_ai',  label: 'Sending to AI',        icon: <Cpu size={14} />,        status: 'pending' },
  { id: 'waiting_for_ai', label: 'Waiting for AI',       icon: <Clock size={14} />,      status: 'pending' },
  { id: 'ai_failed',      label: 'AI Not Responding',    icon: <AlertCircle size={14} />, status: 'hidden' },
  { id: 'trying_new_ai',  label: 'Trying a New AI',      icon: <RefreshCw size={14} />,  status: 'hidden' },
  { id: 'ai_answering',   label: 'AI Answering',         icon: <Brain size={14} />,      status: 'pending' },
  { id: 'preparing_data', label: 'Preparing Data',       icon: <Zap size={14} />,        status: 'pending' },
  { id: 'saving_data',    label: 'Saving Data',          icon: <Database size={14} />,   status: 'pending' },
];

// --- File result state ---
interface FileResult {
  fileName: string;
  data: any;
  status: 'queued' | 'processing' | 'success' | 'error';
  steps: Step[];
  error?: string;
  isSaved?: boolean;
  saveError?: string;
}

// --- Step pipeline component ---
function StepPipeline({ steps }: { steps: Step[] }) {
  const visibleSteps = steps.filter(s => s.status !== 'hidden');
  return (
    <div className="flex flex-wrap gap-2 px-4 pt-4 pb-2">
      {visibleSteps.map((step, idx) => {
        const isLast = idx === visibleSteps.length - 1;
        return (
          <React.Fragment key={step.id}>
            <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-all duration-500
              ${step.status === 'active'  ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-300 animate-pulse' : ''}
              ${step.status === 'done'    ? 'bg-green-100 text-green-700' : ''}
              ${step.status === 'error'   ? 'bg-red-100 text-red-700' : ''}
              ${step.status === 'pending' ? 'bg-gray-100 text-gray-400' : ''}
            `}>
              <span className="flex-shrink-0">
                {step.status === 'done'   && <Check size={12} strokeWidth={3} />}
                {step.status === 'error'  && <X size={12} strokeWidth={3} />}
                {step.status === 'active' && <Loader2 size={12} className="animate-spin" />}
                {step.status === 'pending' && step.icon}
              </span>
              <span>{step.label}</span>
            </div>
            {!isLast && (
              <div className="flex items-center text-gray-300 font-bold text-xs self-center">›</div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// --- Main component ---
export default function UploadPage() {
  const [fileResults, setFileResults] = useState<FileResult[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(-1);

  const blocker = useBlocker(({ nextLocation }) =>
    isUploading && nextLocation.pathname !== window.location.pathname
  );

  useEffect(() => {
    if (blocker.state === 'blocked') {
      toast.error('Please wait for processing to complete.', { id: 'nav-blocked' });
      blocker.reset();
    }
  }, [blocker.state, blocker]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isUploading) { e.preventDefault(); e.returnValue = ''; }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isUploading]);

  // Helper: update a single step in a single file card
  const updateStep = (fileIdx: number, stepId: StepId, newStatus: StepStatus) => {
    setFileResults(prev => {
      const next = [...prev];
      const steps = next[fileIdx].steps.map(s => {
        if (s.id !== stepId) return s;
        return { ...s, status: newStatus };
      });
      next[fileIdx] = { ...next[fileIdx], steps };
      return next;
    });
  };

  // Mark any currently 'active' step as 'done' before activating the next
  const completeActiveStep = (fileIdx: number) => {
    setFileResults(prev => {
      const next = [...prev];
      const steps = next[fileIdx].steps.map(s =>
        s.status === 'active' ? { ...s, status: 'done' as StepStatus } : s
      );
      next[fileIdx] = { ...next[fileIdx], steps };
      return next;
    });
  };

  const processFileSequentially = async (files: File[]) => {
    setIsUploading(true);

    const initialResults: FileResult[] = files.map(f => ({
      fileName: f.name,
      status: 'queued',
      steps: makeSteps(),
      data: null,
    }));
    setFileResults(initialResults);

    for (let i = 0; i < files.length; i++) {
      setCurrentIndex(i);
      setFileResults(prev => {
        const next = [...prev];
        next[i] = { ...next[i], status: 'processing' };
        return next;
      });

      let extractionResult: any = null;
      let extractionError: string | null = null;

      // --- EXTRACTION via SSE ---
      await new Promise<void>((resolve) => {
        uploadInvoiceStreaming(
          files[i],
          // onStep
          (step: string, _detail: string) => {
            completeActiveStep(i);

            // For fallback steps, first un-hide them
            if (step === 'ai_failed' || step === 'trying_new_ai') {
              setFileResults(prev => {
                const next = [...prev];
                const steps = next[i].steps.map(s =>
                  s.id === step ? { ...s, status: 'active' as StepStatus } : s
                );
                next[i] = { ...next[i], steps };
                return next;
              });
            } else {
              updateStep(i, step as StepId, 'active');
            }
          },
          // onResult
          (result: any) => {
            extractionResult = result;
            resolve();
          },
          // onError
          (message: string) => {
            extractionError = message;
            resolve();
          }
        );
      });

      if (extractionError || !extractionResult?.success) {
        // Mark the last active step as error
        setFileResults(prev => {
          const next = [...prev];
          const steps = next[i].steps.map(s =>
            s.status === 'active' ? { ...s, status: 'error' as StepStatus } : s
          );
          next[i] = { ...next[i], status: 'error', steps, error: extractionError ?? extractionResult?.error ?? 'Extraction failed' };
          return next;
        });
        toast.error(`Failed to extract ${files[i].name}`);
        continue;
      }

      // Mark all remaining pending steps as done (extraction complete)
      completeActiveStep(i);

      // --- SAVE step ---
      updateStep(i, 'saving_data', 'active');

      try {
        await saveInvoice(extractionResult.data);
        updateStep(i, 'saving_data', 'done');
        setFileResults(prev => {
          const next = [...prev];
          next[i] = { ...next[i], status: 'success', data: extractionResult, isSaved: true };
          return next;
        });
      } catch (saveErr: any) {
        updateStep(i, 'saving_data', 'error');
        setFileResults(prev => {
          const next = [...prev];
          next[i] = { ...next[i], status: 'success', data: extractionResult, isSaved: false, saveError: String(saveErr?.message ?? saveErr) };
          return next;
        });
        toast.error(`Auto-save failed for ${files[i].name}. You can retry manually.`);
      }
    }

    setIsUploading(false);
    setCurrentIndex(-1);
    toast.success('Batch processing complete!');
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    await processFileSequentially(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: isUploading,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpeg', '.jpg'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
    }
  });

  const handleRetrySave = async (index: number) => {
    const result = fileResults[index];
    if (!result.data?.data) return;

    setFileResults(prev => {
      const next = [...prev];
      const steps = next[index].steps.map(s =>
        s.id === 'saving_data' ? { ...s, status: 'active' as StepStatus } : s
      );
      next[index] = { ...next[index], steps, saveError: undefined };
      return next;
    });

    try {
      await saveInvoice(result.data.data);
      setFileResults(prev => {
        const next = [...prev];
        const steps = next[index].steps.map(s =>
          s.id === 'saving_data' ? { ...s, status: 'done' as StepStatus } : s
        );
        next[index] = { ...next[index], steps, isSaved: true };
        return next;
      });
      toast.success('Saved successfully!');
    } catch {
      setFileResults(prev => {
        const next = [...prev];
        const steps = next[index].steps.map(s =>
          s.id === 'saving_data' ? { ...s, status: 'error' as StepStatus } : s
        );
        next[index] = { ...next[index], steps, saveError: 'Save failed again.' };
        return next;
      });
      toast.error('Save failed again.');
    }
  };

  const handleClear = () => setFileResults([]);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Upload Invoices</h1>
        <p className="text-gray-500">AI-powered extraction with live progress tracking — one file at a time.</p>
      </div>

      {fileResults.length === 0 && (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50'}
            ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-blue-100 rounded-full text-blue-600">
              <UploadCloud size={40} />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive ? 'Drop your invoices here...' : 'Drag & drop invoices here'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Watch the live AI pipeline for each file</p>
            </div>
            <button disabled={isUploading} className="px-6 py-2.5 bg-white border border-gray-300 rounded-lg shadow-sm text-gray-700 font-medium hover:bg-gray-50 transition-colors disabled:opacity-50">
              Browse Files
            </button>
            <p className="text-xs text-gray-400">Supported: PDF, PNG, JPG/JPEG, DOCX, TXT</p>
          </div>
        </div>
      )}

      {isUploading && (
        <div className="bg-white border-2 border-blue-100 rounded-2xl p-6 text-center shadow-md space-y-3">
          <Loader2 className="animate-spin text-blue-500 mx-auto" size={40} />
          <h3 className="text-lg font-semibold text-gray-800">
            Processing file {currentIndex + 1} of {fileResults.length}
          </h3>
          <div className="w-full bg-gray-100 h-1.5 rounded-full max-w-sm mx-auto overflow-hidden">
            <div
              className="bg-blue-500 h-full transition-all duration-500"
              style={{ width: `${((currentIndex + 1) / fileResults.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {fileResults.length > 0 && !isUploading && (
        <div className="mb-4 flex justify-between items-center bg-green-50 text-green-800 border border-green-200 px-4 py-3 rounded-xl">
          <div className="flex items-center space-x-2">
            <CheckCircle size={18} />
            <span className="font-medium text-sm">
              Done — {fileResults.filter(f => f.isSaved).length} of {fileResults.length} saved.
            </span>
          </div>
          <button onClick={handleClear} className="text-xs font-semibold bg-white px-3 py-1.5 rounded border border-green-200 hover:bg-green-50 transition-colors">
            Clear & Upload More
          </button>
        </div>
      )}

      <div className="space-y-6">
        {fileResults.map((result, idx) => (
          <div key={idx} className={`bg-white rounded-2xl border transition-all duration-300 overflow-hidden shadow-sm
            ${currentIndex === idx ? 'border-blue-400 ring-2 ring-blue-100 shadow-md' : 'border-gray-200'}`}
          >
            {/* Header */}
            <div className={`flex items-center justify-between px-4 py-3 border-b ${currentIndex === idx ? 'bg-blue-50/40' : 'bg-gray-50/50'}`}>
              <div className="flex items-center space-x-2">
                <FileText size={18} className={currentIndex === idx ? 'text-blue-500' : 'text-gray-400'} />
                <span className="font-semibold text-gray-800 text-sm truncate max-w-xs">{result.fileName}</span>
                {result.status === 'queued' && (
                  <span className="text-[10px] uppercase tracking-wider font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Queued</span>
                )}
                {result.isSaved && (
                  <span className="text-[10px] uppercase tracking-wider font-bold bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Check size={9} strokeWidth={3} /> Saved
                  </span>
                )}
                {result.status === 'error' && (
                  <span className="text-[10px] uppercase tracking-wider font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Failed</span>
                )}
              </div>
              {result.saveError && (
                <button
                  onClick={() => handleRetrySave(idx)}
                  className="flex items-center space-x-1 text-xs font-bold text-orange-600 hover:bg-orange-50 px-2 py-1 rounded transition-colors"
                >
                  <RotateCcw size={12} />
                  <span>Retry Save</span>
                </button>
              )}
            </div>

            {/* Step pipeline */}
            {result.status !== 'queued' && (
              <StepPipeline steps={result.steps} />
            )}

            {/* Extracted data */}
            <div>
              {result.status === 'success' && result.data && (
                <div className="animate-in fade-in duration-500">
                  <ExtractedDataDisplay
                    data={result.data.data}
                    showSaveButton={!result.isSaved}
                    initialSaved={result.isSaved}
                  />
                </div>
              )}
              {result.status === 'error' && result.error && (
                <div className="p-6 text-center space-y-2">
                  <AlertCircle size={32} className="text-red-400 mx-auto" />
                  <p className="text-red-600 text-sm font-medium">{result.error}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
