import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Zap, 
  Cpu, 
  Layers, 
  FileCheck, 
  Loader2,
  AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getStats } from '../services/api';

interface StatsData {
  total_processed: number;
  cache_hits: number;
  cache_misses: number;
  regex_only: number;
  regex_plus_ai: number;
  ai_only: number;
  estimated_tokens_saved: number;
}

export default function StatsPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      const data = await getStats();
      setStats(data);
    } catch (err) {
      toast.error('Failed to load system statistics');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="animate-spin text-blue-500 mb-4" size={40} />
        <p className="text-gray-500">Loading dashboard statistics...</p>
      </div>
    );
  }

  if (!stats) return null;

  const cacheHitRate = stats.total_processed > 0 
    ? (stats.cache_hits / stats.total_processed * 100).toFixed(1) 
    : '0';

  const regexOnlyRate = stats.cache_misses > 0 
    ? (stats.regex_only / stats.cache_misses * 100).toFixed(1) 
    : '0';

  const regexPlusAiRate = stats.cache_misses > 0 
    ? (stats.regex_plus_ai / stats.cache_misses * 100).toFixed(1) 
    : '0';

  const aiOnlyRate = stats.cache_misses > 0 
    ? (stats.ai_only / stats.cache_misses * 100).toFixed(1) 
    : '0';

  const StatCard = ({ title, value, subtext, icon: Icon, color }: any) => (
    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon size={24} />
        </div>
      </div>
      <div>
        <h3 className="text-gray-500 text-sm font-medium mb-1">{title}</h3>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Performance</h1>
          <p className="text-gray-500 mt-1">Real-time statistics on invoice processing and AI efficiency.</p>
        </div>
        <button 
          onClick={fetchStats}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
        >
          Refresh Data
        </button>
      </div>

      {/* Top Row Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Processed" 
          value={stats.total_processed} 
          subtext="Total upload attempts" 
          icon={FileCheck} 
          color="bg-blue-50 text-blue-600"
        />
        <StatCard 
          title="Cache Hit Rate" 
          value={`${cacheHitRate}%`} 
          subtext={`${stats.cache_hits} hits from cache`} 
          icon={TrendingUp} 
          color="bg-green-50 text-green-600"
        />
        <StatCard 
          title="Tokens Saved" 
          value={stats.estimated_tokens_saved.toLocaleString()} 
          subtext="Estimated efficiency gain" 
          icon={Zap} 
          color="bg-amber-50 text-amber-600"
        />
        <StatCard 
          title="Total Misses" 
          value={stats.cache_misses} 
          subtext="Processed by workflow" 
          icon={AlertCircle} 
          color="bg-slate-50 text-slate-600"
        />
      </div>

      {/* Extraction Breakdown */}
      <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
        <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <BarChart3 className="text-blue-500" />
          Extraction Method Breakdown (New Processing)
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Regex Only */}
          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <p className="text-sm font-medium text-gray-500">Regex Only</p>
                <p className="text-2xl font-bold text-green-600">{stats.regex_only}</p>
              </div>
              <span className="text-xs font-bold bg-green-50 text-green-700 px-2 py-1 rounded">
                {regexOnlyRate}%
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${regexOnlyRate}%` }}></div>
            </div>
            <p className="text-xs text-gray-400">0 Tokens used. Maximum cost efficiency.</p>
          </div>

          {/* Regex + AI */}
          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <p className="text-sm font-medium text-gray-500">Regex + AI</p>
                <p className="text-2xl font-bold text-blue-600">{stats.regex_plus_ai}</p>
              </div>
              <span className="text-xs font-bold bg-blue-50 text-blue-700 px-2 py-1 rounded">
                {regexPlusAiRate}%
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${regexPlusAiRate}%` }}></div>
            </div>
            <p className="text-xs text-gray-400">Hybrid extraction. Optimized token usage.</p>
          </div>

          {/* AI Only */}
          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <p className="text-sm font-medium text-gray-500">AI Only (Vision)</p>
                <p className="text-2xl font-bold text-slate-600">{stats.ai_only}</p>
              </div>
              <span className="text-xs font-bold bg-slate-50 text-slate-700 px-2 py-1 rounded">
                {aiOnlyRate}%
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-slate-500 h-2 rounded-full" style={{ width: `${aiOnlyRate}%` }}></div>
            </div>
            <p className="text-xs text-gray-400">Full LLM processing (Images & Scans).</p>
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 flex gap-4">
          <Cpu className="text-blue-600 shrink-0" size={32} />
          <div>
            <h4 className="font-bold text-blue-900 mb-1">Intelligent Routing</h4>
            <p className="text-blue-800/80 text-sm">
              Our system automatically decides the most cost-effective way to process each invoice, 
              using Python-based Regex for digital documents and Gemini 1.5 Flash Vision for complex images.
            </p>
          </div>
        </div>
        <div className="bg-green-50 p-6 rounded-2xl border border-green-100 flex gap-4">
          <Layers className="text-green-600 shrink-0" size={32} />
          <div>
            <h4 className="font-bold text-green-900 mb-1">Efficient Caching</h4>
            <p className="text-green-800/80 text-sm">
              Identical files are detected via SHA-256 hashing, bypassing the processing pipeline 
              entirely to deliver sub-second response times and zero token cost.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
