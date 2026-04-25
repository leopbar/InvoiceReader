import React, { useCallback, useState, useEffect } from 'react';
import { useBlocker } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileText, Loader2, CheckCircle, AlertCircle, Save, RotateCcw } from 'lucide-react';
import toast from 'react-hot-toast';
import { uploadInvoice, saveInvoice } from '../services/api';
import ExtractedDataDisplay from '../components/ExtractedDataDisplay';

interface FileResult {
  fileName: string;
  data: any;
  status: 'processing' | 'success' | 'error';
  subStatus?: 'extracting' | 'saving' | 'saved' | 'failed' | 'save-failed';
  error?: string;
  isSaved?: boolean;
}

export default function UploadPage() {
  const [fileResults, setFileResults] = useState<FileResult[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(-1);

  const blocker = useBlocker(({ nextLocation }) => {
    return isUploading && nextLocation.pathname !== window.location.pathname;
  });

  // Handle blocked navigation
  useEffect(() => {
    if (blocker.state === 'blocked') {
      toast.error(
        "Navigation Blocked: Please wait for processing to complete.",
        { id: 'nav-blocked' }
      );
      blocker.reset();
    }
  }, [blocker.state, blocker]);

  // Prevent browser refresh/close while uploading
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isUploading) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isUploading]);

  const processFileSequentially = async (files: File[]) => {
    setIsUploading(true);
    
    // Initialize results array
    const initialResults: FileResult[] = files.map(file => ({
      fileName: file.name,
      status: 'processing',
      subStatus: 'extracting',
      data: null
    }));
    setFileResults(initialResults);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setCurrentIndex(i);
      
      try {
        // Step 1: Extraction
        setFileResults(prev => {
          const next = [...prev];
          next[i] = { ...next[i], subStatus: 'extracting' };
          return next;
        });
        
        const extractionResult = await uploadInvoice(file);
        
        // Step 2: Auto-save
        setFileResults(prev => {
          const next = [...prev];
          next[i] = { ...next[i], subStatus: 'saving', data: extractionResult };
          return next;
        });

        try {
          await saveInvoice(extractionResult.data);
          setFileResults(prev => {
            const next = [...prev];
            next[i] = { ...next[i], status: 'success', subStatus: 'saved', isSaved: true };
            return next;
          });
        } catch (saveError) {
          console.error(`Auto-save failed for ${file.name}:`, saveError);
          setFileResults(prev => {
            const next = [...prev];
            next[i] = { ...next[i], status: 'success', subStatus: 'save-failed', isSaved: false };
            return next;
          });
          toast.error(`Auto-save failed for ${file.name}. You can save it manually.`);
        }

      } catch (error: any) {
        const detail = error.response?.data?.detail;
        const msg = detail?.message ?? (typeof detail === 'string' ? detail : 'Extraction failed');
        setFileResults(prev => {
          const next = [...prev];
          next[i] = { ...next[i], status: 'error', subStatus: 'failed', error: msg };
          return next;
        });
        toast.error(`Failed to extract ${file.name}`);
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
      'text/plain': ['.txt']
    }
  });

  const handleRetrySave = async (index: number) => {
    const result = fileResults[index];
    if (!result.data?.data) return;

    setFileResults(prev => {
      const next = [...prev];
      next[index] = { ...next[index], subStatus: 'saving' };
      return next;
    });

    try {
      await saveInvoice(result.data.data);
      setFileResults(prev => {
        const next = [...prev];
        next[index] = { ...next[index], subStatus: 'saved', isSaved: true };
        return next;
      });
      toast.success('Saved successfully!');
    } catch (err) {
      setFileResults(prev => {
        const next = [...prev];
        next[index] = { ...next[index], subStatus: 'save-failed', isSaved: false };
        return next;
      });
      toast.error('Save failed again.');
    }
  };

  const handleClear = () => {
    setFileResults([]);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Upload Invoices</h1>
        <p className="text-gray-500">Processing invoices one by one ensures maximum AI accuracy and database stability.</p>
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
              <p className="text-sm text-gray-500 mt-1">Files are processed sequentially to prevent errors</p>
            </div>
            
            <button disabled={isUploading} className="px-6 py-2.5 bg-white border border-gray-300 rounded-lg shadow-sm text-gray-700 font-medium hover:bg-gray-50 transition-colors disabled:opacity-50">
              Browse Files
            </button>
            
            <p className="text-xs text-gray-400 mt-4">
              Supported formats: PDF, PNG, JPG/JPEG, DOCX, TXT
            </p>
          </div>
        </div>
      )}

      {isUploading && (
        <div className="bg-white border-2 border-blue-100 rounded-2xl p-8 text-center shadow-md space-y-4">
          <Loader2 className="animate-spin text-blue-500 mx-auto" size={48} />
          <h3 className="text-xl font-semibold text-gray-800">
            Processing file {currentIndex + 1} of {fileResults.length}
          </h3>
          <div className="w-full bg-gray-100 h-2 rounded-full max-w-md mx-auto overflow-hidden">
            <div 
              className="bg-blue-500 h-full transition-all duration-500" 
              style={{ width: `${((currentIndex + 1) / fileResults.length) * 100}%` }}
            />
          </div>
          <p className="text-sm text-gray-500">Currently processing: <span className="font-medium text-gray-700">{fileResults[currentIndex]?.fileName}</span></p>
        </div>
      )}

      {fileResults.length > 0 && !isUploading && (
        <div className="mb-6 flex justify-between items-center bg-green-50 text-green-800 border border-green-200 px-4 py-3 rounded-lg animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center space-x-2">
             <CheckCircle size={20} />
             <span className="font-medium">All processing complete! {fileResults.filter(f => f.subStatus === 'saved').length} saved successfully.</span>
          </div>
          <button 
             onClick={handleClear}
             className="text-sm font-medium bg-white px-3 py-1.5 rounded border border-green-200 hover:bg-green-50 transition-colors shadow-sm"
          >
             Clear Results & Upload More
          </button>
        </div>
      )}

      <div className="space-y-6">
        {fileResults.map((result, idx) => (
          <div key={idx} className={`bg-white rounded-2xl border transition-all duration-300 overflow-hidden
            ${currentIndex === idx ? 'border-blue-400 shadow-lg ring-2 ring-blue-50' : 'border-gray-200 shadow-sm'}`}>
            
            <div className={`flex items-center justify-between p-4 border-b ${currentIndex === idx ? 'bg-blue-50/50' : 'bg-gray-50/50'}`}>
                <div className="flex items-center space-x-3">
                  <FileText className={currentIndex === idx ? 'text-blue-600' : 'text-gray-400'} />
                  <h3 className="font-semibold text-gray-800">{result.fileName}</h3>
                  
                  {/* Granular Status Tags */}
                  {result.subStatus === 'extracting' && (
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full flex items-center space-x-1">
                      <Loader2 size={10} className="animate-spin"/> <span>Extracting...</span>
                    </span>
                  )}
                  {result.subStatus === 'saving' && (
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full flex items-center space-x-1">
                      <Loader2 size={10} className="animate-spin"/> <span>Saving...</span>
                    </span>
                  )}
                  {result.subStatus === 'saved' && (
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center space-x-1">
                      <CheckCircle size={10}/> <span>Saved ✓</span>
                    </span>
                  )}
                  {result.subStatus === 'save-failed' && (
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full flex items-center space-x-1">
                      <AlertCircle size={10}/> <span>Save Failed</span>
                    </span>
                  )}
                  {result.subStatus === 'failed' && (
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full flex items-center space-x-1">
                      <AlertCircle size={10}/> <span>Failed</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  {result.subStatus === 'save-failed' && (
                    <button 
                      onClick={() => handleRetrySave(idx)}
                      className="flex items-center space-x-1 text-xs font-bold text-orange-600 hover:bg-orange-50 px-2 py-1 rounded transition-colors"
                    >
                      <RotateCcw size={12} />
                      <span>Retry Save</span>
                    </button>
                  )}
                </div>
            </div>
            
            <div className="p-0">
              {result.status === 'success' && result.data && (
                <div className="animate-in fade-in duration-500">
                  <ExtractedDataDisplay 
                    data={result.data.data} 
                    showSaveButton={true}
                    initialSaved={result.isSaved}
                  />
                </div>
              )}
              {result.status === 'error' && (
                <div className="p-8 text-center space-y-3">
                  <AlertCircle size={40} className="text-red-400 mx-auto" />
                  <p className="text-red-600 font-medium">{result.error}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
