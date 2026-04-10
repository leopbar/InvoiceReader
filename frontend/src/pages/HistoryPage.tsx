import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, FileText, Settings, Copy, Download, FileDown, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { getInvoices, deleteInvoices } from '../services/api';

const getAddress = (inv: any, type: string) => {
  if (!inv.invoice_addresses) return {};
  return inv.invoice_addresses.find((a: any) => a.address_type === type) || {};
};

type ColumnDef = {
  id: string;
  group: string;
  label: string;
  getValue: (inv: any) => any;
};

const COLUMNS: ColumnDef[] = [
  // Invoice Info
  { id: 'invoice_number', group: 'Invoice Info', label: 'Invoice Number', getValue: inv => inv.invoice_number },
  { id: 'invoice_date', group: 'Invoice Info', label: 'Invoice Date', getValue: inv => inv.invoice_date },
  { id: 'due_date', group: 'Invoice Info', label: 'Due Date', getValue: inv => inv.due_date },
  { id: 'currency', group: 'Invoice Info', label: 'Currency', getValue: inv => inv.currency },
  { id: 'payment_terms', group: 'Invoice Info', label: 'Payment Terms', getValue: inv => inv.payment_terms },
  { id: 'purchase_order', group: 'Invoice Info', label: 'PO Number', getValue: inv => inv.purchase_order },
  { id: 'status', group: 'Invoice Info', label: 'Status', getValue: inv => inv.status },
  
  // Supplier
  { id: 'supplier_name', group: 'Supplier', label: 'Supplier Name', getValue: inv => inv.suppliers?.name },
  { id: 'supplier_address', group: 'Supplier', label: 'Supplier Address', getValue: inv => inv.suppliers?.address },
  { id: 'supplier_email', group: 'Supplier', label: 'Supplier Email', getValue: inv => inv.suppliers?.email },
  { id: 'supplier_phone', group: 'Supplier', label: 'Supplier Phone', getValue: inv => inv.suppliers?.phone },
  { id: 'supplier_tax_id', group: 'Supplier', label: 'Supplier Tax ID', getValue: inv => inv.suppliers?.tax_id },

  // Bill To
  { id: 'bill_company', group: 'Bill To', label: 'Company Name', getValue: inv => getAddress(inv, 'bill_to').company_name },
  { id: 'bill_address', group: 'Bill To', label: 'Address', getValue: inv => getAddress(inv, 'bill_to').address_line },
  { id: 'bill_city', group: 'Bill To', label: 'City', getValue: inv => getAddress(inv, 'bill_to').city },
  { id: 'bill_state', group: 'Bill To', label: 'State', getValue: inv => getAddress(inv, 'bill_to').state },
  { id: 'bill_zip', group: 'Bill To', label: 'ZIP Code', getValue: inv => getAddress(inv, 'bill_to').zip_code },
  { id: 'bill_country', group: 'Bill To', label: 'Country', getValue: inv => getAddress(inv, 'bill_to').country },

  // Ship To
  { id: 'ship_company', group: 'Ship To', label: 'Company Name', getValue: inv => getAddress(inv, 'ship_to').company_name },
  { id: 'ship_address', group: 'Ship To', label: 'Address', getValue: inv => getAddress(inv, 'ship_to').address_line },
  { id: 'ship_city', group: 'Ship To', label: 'City', getValue: inv => getAddress(inv, 'ship_to').city },
  { id: 'ship_state', group: 'Ship To', label: 'State', getValue: inv => getAddress(inv, 'ship_to').state },
  { id: 'ship_zip', group: 'Ship To', label: 'ZIP Code', getValue: inv => getAddress(inv, 'ship_to').zip_code },
  { id: 'ship_country', group: 'Ship To', label: 'Country', getValue: inv => getAddress(inv, 'ship_to').country },

  // Totals
  { id: 'subtotal', group: 'Totals', label: 'Subtotal', getValue: inv => inv.subtotal },
  { id: 'tax_amount', group: 'Totals', label: 'Tax Amount', getValue: inv => inv.tax_amount },
  { id: 'discount', group: 'Totals', label: 'Discount', getValue: inv => inv.discount },
  { id: 'total_amount', group: 'Totals', label: 'Total Amount', getValue: inv => inv.total_amount },

  // Other
  { id: 'notes', group: 'Other', label: 'Notes', getValue: inv => inv.notes },
  { id: 'original_filename', group: 'Other', label: 'Original Filename', getValue: inv => inv.original_filename },
  { id: 'file_type', group: 'Other', label: 'File Type', getValue: inv => inv.file_type },
];

const DEFAULT_COLUMNS = ['invoice_number', 'supplier_name', 'invoice_date', 'total_amount', 'status'];

export default function HistoryPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const navigate = useNavigate();

  // Column Selector State
  const [selectedColIds, setSelectedColIds] = useState<string[]>(DEFAULT_COLUMNS);
  const [showConfig, setShowConfig] = useState(false);
  const configRef = useRef<HTMLDivElement>(null);

  // Load saved preferences on mount
  useEffect(() => {
    const saved = localStorage.getItem('invoice_table_cols');
    if (saved) {
      try {
        setSelectedColIds(JSON.parse(saved));
      } catch (e) {
        // Fallback
      }
    }
    fetchInvoices();

    // Close config dropdown when clicking outside
    const handleClickOutside = (e: MouseEvent) => {
      if (configRef.current && !configRef.current.contains(e.target as Node)) {
        setShowConfig(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchInvoices = async () => {
    try {
      const data = await getInvoices();
      setInvoices(data.invoices || []);
    } catch (err) {
      toast.error('Failed to load invoices');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleColumn = (id: string) => {
    setSelectedColIds(prev => {
      let newCols;
      if (prev.includes(id)) {
        newCols = prev.filter(c => c !== id);
      } else {
        newCols = [...prev, id];
      }
      localStorage.setItem('invoice_table_cols', JSON.stringify(newCols));
      return newCols;
    });
  };

  const resetColumns = () => {
    setSelectedColIds(DEFAULT_COLUMNS);
    localStorage.setItem('invoice_table_cols', JSON.stringify(DEFAULT_COLUMNS));
  };

  const activeColumns = COLUMNS.filter(col => selectedColIds.includes(col.id));

  // Groups for UI rendering
  const colGroups = COLUMNS.reduce((acc, col) => {
    if (!acc[col.group]) acc[col.group] = [];
    acc[col.group].push(col);
    return acc;
  }, {} as Record<string, ColumnDef[]>);

  const copyColumn = (col: ColumnDef, e: React.MouseEvent) => {
    e.stopPropagation(); // prevent row click
    const values = invoices.map(inv => col.getValue(inv) || '');
    navigator.clipboard.writeText(values.join('\n'));
    toast.success('Column copied!');
  };

  const toggleSelectAll = () => {
    if (selectedInvoices.length === invoices.length) {
      setSelectedInvoices([]);
    } else {
      setSelectedInvoices(invoices.map(inv => inv.id));
    }
  };

  const toggleSelectInvoice = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedInvoices(prev => 
      prev.includes(id) ? prev.filter(invId => invId !== id) : [...prev, id]
    );
  };

  const handleDeleteSelected = async () => {
    if (selectedInvoices.length === 0) return;
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteInvoices(selectedInvoices);
      toast.success(`Successfully deleted ${selectedInvoices.length} invoice(s)`);
      setSelectedInvoices([]);
      fetchInvoices();
    } catch (err) {
      toast.error('Failed to delete invoices');
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  const copyAllVisible = () => {
    if (invoices.length === 0) return;
    
    // Header row
    const headers = activeColumns.map(c => c.label).join('\t');
    
    // Data rows
    const rows = invoices.map(inv => {
      return activeColumns.map(col => {
        const val = col.getValue(inv);
        // Replace tabs and newlines to prevent breaking TSV format
        if (typeof val === 'string') return val.replace(/\t|\n/g, ' ');
        return val || '';
      }).join('\t');
    });

    const finalString = [headers, ...rows].join('\n');
    navigator.clipboard.writeText(finalString);
    toast.success('All visible data copied to clipboard!');
  };

  const downloadCSV = () => {
    if (invoices.length === 0) return;
    
    const BOM = '\uFEFF';
    
    // Header row
    const headers = activeColumns.map(c => `"${c.label.replace(/"/g, '""')}"`).join(',');
    
    // Data rows
    const rows = invoices.map(inv => {
      return activeColumns.map(col => {
        const val = col.getValue(inv);
        let strVal = val === null || val === undefined ? '' : String(val);
        // Escape quotes
        strVal = strVal.replace(/"/g, '""');
        // Wrap in quotes
        return `"${strVal}"`;
      }).join(',');
    });

    const csvContent = BOM + [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // Create download link
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    
    const dateStr = new Date().toISOString().split('T')[0];
    link.setAttribute('download', `invoices_${dateStr}.csv`);
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    toast.success('CSV downloaded!');
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="animate-spin text-blue-500 mb-4" size={40} />
        <p className="text-gray-500">Loading invoice history...</p>
      </div>
    );
  }

  return (
    <div className="max-w-[95%] mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Invoice History</h1>
          <p className="text-gray-500 mt-1">
            Showing {invoices.length} {invoices.length === 1 ? 'invoice' : 'invoices'}
          </p>
        </div>
        
        <div className="flex items-center space-x-3 relative">
          {selectedInvoices.length > 0 && (
            <button
              onClick={handleDeleteSelected}
              disabled={isDeleting}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition shadow-sm disabled:opacity-50 mr-2"
            >
              {isDeleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
              <span>Delete Selected ({selectedInvoices.length})</span>
            </button>
          )}

          <button
            onClick={downloadCSV}
            className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition shadow-sm"
          >
            <FileDown size={16} />
            <span>Download CSV</span>
          </button>

          <button
            onClick={copyAllVisible}
            className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition shadow-sm"
          >
            <Copy size={16} />
            <span>Copy All Visible Data</span>
          </button>
          
          <div ref={configRef} className="relative">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition shadow-sm"
            >
              <Settings size={16} />
              <span>Customize Columns</span>
            </button>
            
            {showConfig && (
              <div className="absolute right-0 mt-2 w-[500px] bg-white border border-gray-200 rounded-xl shadow-2xl z-50 flex flex-col max-h-[70vh]">
                <div className="p-4 border-b flex justify-between items-center bg-gray-50 rounded-t-xl">
                  <h3 className="font-bold text-gray-800">Available Columns</h3>
                  <button 
                    onClick={resetColumns}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Reset to Default
                  </button>
                </div>
                
                <div className="p-5 overflow-y-auto grid grid-cols-2 gap-x-6 gap-y-8">
                  {Object.entries(colGroups).map(([groupName, cols]) => (
                    <div key={groupName} className="space-y-3">
                      <h4 className="font-semibold text-gray-900 text-sm uppercase tracking-wider">{groupName}</h4>
                      <div className="space-y-2">
                        {cols.map(col => (
                          <label key={col.id} className="flex items-center space-x-2 cursor-pointer group">
                            <input 
                              type="checkbox"
                              checked={selectedColIds.includes(col.id)}
                              onChange={() => toggleColumn(col.id)}
                              className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-gray-300 cursor-pointer"
                            />
                            <span className="text-sm text-gray-700 group-hover:text-blue-600 transition-colors">
                              {col.label}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {invoices.length === 0 ? (
        <div className="bg-white border rounded-xl p-16 text-center shadow-sm space-y-4">
          <div className="bg-gray-50 p-4 rounded-full inline-block">
            <FileText size={48} className="text-gray-400" />
          </div>
          <h3 className="text-xl font-medium text-gray-800">No invoices yet</h3>
          <p className="text-gray-500">Go to the upload page to process and save your first invoice.</p>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
          >
            Upload Now
          </button>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead className="bg-gray-50 sticky top-0 z-10 border-b border-gray-200 shadow-sm">
                <tr>
                  <th className="px-4 py-4 w-12 text-center border-r border-gray-100">
                    <input 
                      type="checkbox"
                      checked={invoices.length > 0 && selectedInvoices.length === invoices.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-gray-300 cursor-pointer"
                    />
                  </th>
                  {activeColumns.map(col => (
                    <th key={col.id} className="px-6 py-4 font-semibold text-gray-700 text-sm group relative">
                      <div className="flex items-center justify-between space-x-2">
                        <span>{col.label}</span>
                        <button 
                          onClick={(e) => copyColumn(col, e)}
                          title={`Copy all ${col.label} data`}
                          className="text-gray-400 hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Copy size={14} />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {invoices.map((inv, idx) => (
                  <tr 
                    key={inv.id} 
                    onClick={() => navigate(`/invoice/${inv.id}`)}
                    className={`cursor-pointer transition-colors hover:bg-blue-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'} ${selectedInvoices.includes(inv.id) ? 'bg-blue-50/70 border-l-4 border-l-blue-500' : 'border-l-4 border-transparent'}`}
                  >
                    <td className="px-4 py-3 text-center border-r border-gray-50" onClick={e => e.stopPropagation()}>
                      <input 
                        type="checkbox"
                        checked={selectedInvoices.includes(inv.id)}
                        onChange={(e) => toggleSelectInvoice(inv.id, e as any)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-gray-300 cursor-pointer"
                      />
                    </td>
                    {activeColumns.map(col => {
                      const val = col.getValue(inv);
                      // Custom rendering for specifics
                      let displayVal = val || '-';
                      
                      // Format currency for certain fields
                      if (['total_amount', 'subtotal', 'tax_amount', 'discount'].includes(col.id) && val !== null && val !== undefined) {
                        displayVal = new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: inv.currency || 'USD'
                        }).format(Number(val));
                      }

                      if (col.id === 'status') {
                        return (
                          <td key={col.id} className="px-6 py-3">
                            <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full capitalize">
                              {val || 'processed'}
                            </span>
                          </td>
                        );
                      }
                      
                      return (
                        <td key={col.id} className="px-6 py-3 font-medium text-gray-600 text-sm max-w-[300px] truncate" title={String(val)}>
                          {displayVal}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Custom Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6">
              <div className="flex flex-col items-center text-center space-y-4 mb-6">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center text-red-600">
                  <Trash2 size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Delete Invoices</h3>
                  <p className="text-gray-500 mt-2 text-[15px]">
                    Are you sure you want to delete <span className="font-bold text-gray-800">{selectedInvoices.length}</span> selected invoice{selectedInvoices.length === 1 ? '' : 's'}? 
                    This action cannot be undone.
                  </p>
                </div>
              </div>
              <div className="flex space-x-3 w-full">
                <button 
                  onClick={() => setShowDeleteModal(false)}
                  disabled={isDeleting}
                  className="w-1/2 py-2.5 text-gray-700 font-medium hover:bg-gray-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={confirmDelete}
                  disabled={isDeleting}
                  className="w-1/2 py-2.5 bg-red-600 text-white font-medium hover:bg-red-700 rounded-xl transition flex text-center justify-center items-center space-x-2 disabled:opacity-50"
                >
                  {isDeleting ? <Loader2 size={18} className="animate-spin" /> : <span>Yes, Delete</span>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
