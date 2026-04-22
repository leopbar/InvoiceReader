import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileText, Loader2, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { uploadInvoice } from '../services/api';
import ExtractedDataDisplay from '../components/ExtractedDataDisplay';

interface FileResult {
  fileName: string;
  data: any;
  status: 'processing' | 'success' | 'error';
  error?: string;
}

export default function UploadPage() {
  const [fileResults, setFileResults] = useState<FileResult[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    setIsUploading(true);
    
    // Initialize results array with processing status
    const initialResults: FileResult[] = acceptedFiles.map(file => ({
      fileName: file.name,
      status: 'processing',
      data: null
    }));
    
    setFileResults(initialResults);
    
    // Process files continuously
    const processFile = async (file: File, index: number) => {
      try {
        const data = await uploadInvoice(file);
        setFileResults(prev => {
          const newResults = [...prev];
          newResults[index] = { ...newResults[index], status: 'success', data };
          return newResults;
        });
        
        if (data.saved) {
          toast.success(`${file.name}: Extracted and saved!`);
        } else {
          toast.success(`${file.name}: Extracted (Save pending)`);
        }
      } catch (error: any) {
        setFileResults(prev => {
          const newResults = [...prev];
          const msg = error.response?.data?.detail || 'Failed to process invoice';
          newResults[index] = { ...newResults[index], status: 'error', error: msg };
          return newResults;
        });
        toast.error(`Failed to process ${file.name}`);
      }
    };

    // Process all files async
    await Promise.all(acceptedFiles.map((file, i) => processFile(file, i)));
    
    setIsUploading(false);
    toast.success('Batch processing complete!');
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpeg', '.jpg'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt']
    }
  });

  const handleClear = () => {
    setFileResults([]);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Upload Invoices</h1>
        <p className="text-gray-500">Let our AI instantly extract details from one or multiple invoices in sequence.</p>
      </div>

      {fileResults.length === 0 && (
        <div 
          {...getRootProps()} 
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50'}`}
        >
          <input {...getInputProps()} />
          
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-blue-100 rounded-full text-blue-600">
              <UploadCloud size={40} />
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive ? 'Drop your invoices here...' : 'Drag & drop multiple invoices here'}
              </p>
              <p className="text-sm text-gray-500 mt-1">or click to browse from your computer</p>
            </div>
            
            <button className="px-6 py-2.5 bg-white border border-gray-300 rounded-lg shadow-sm text-gray-700 font-medium hover:bg-gray-50 transition-colors">
              Browse Files
            </button>
            
            <p className="text-xs text-gray-400 mt-4">
              Supported formats: PDF, PNG, JPG/JPEG, DOCX, TXT
            </p>
          </div>
        </div>
      )}

      {isUploading && (
        <div className="bg-white border rounded-2xl p-8 text-center shadow-sm space-y-4">
          <Loader2 className="animate-spin text-blue-500 mx-auto" size={48} />
          <h3 className="text-xl font-semibold text-gray-800">Analyzing your invoices with AI...</h3>
          <p className="text-sm text-gray-500">Please wait while we process {fileResults.length} file(s).</p>
        </div>
      )}

      {fileResults.length > 0 && !isUploading && (
        <div className="mb-6 flex justify-between items-center bg-green-50 text-green-800 border border-green-200 px-4 py-3 rounded-lg">
          <div className="flex items-center space-x-2">
             <CheckCircle size={20} />
             <span className="font-medium">Batch processing successfully completed!</span>
          </div>
          <button 
             onClick={handleClear}
             className="text-sm font-medium bg-white px-3 py-1.5 rounded border border-green-200 hover:bg-green-50 transition-colors"
          >
             Upload More Files
          </button>
        </div>
      )}

      <div className="space-y-8">
        {fileResults.map((result, idx) => (
          <div key={idx} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex items-center space-x-3 p-4 border-b bg-gray-50">
                <FileText className="text-blue-500" />
                <h3 className="font-semibold text-lg text-gray-800">{result.fileName}</h3>
                
                {result.status === 'processing' && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full flex items-center space-x-1">
                    <Loader2 size={12} className="animate-spin"/> <span>Processing...</span>
                  </span>
                )}
                
                {result.status === 'success' && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Success</span>
                )}
                
                {result.status === 'error' && (
                  <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">Failed: {result.error}</span>
                )}
            </div>
            
            <div className="p-6">
              {result.status === 'success' && result.data && (
                  <ExtractedDataDisplay data={result.data} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
