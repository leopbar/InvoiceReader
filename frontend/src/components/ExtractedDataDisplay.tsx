import React, { useState } from 'react';
import { Copy, CheckCircle, Save, AlertCircle, RotateCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { saveInvoice } from '../services/api';

interface ExtractedDataDisplayProps {
  data: any;
  showSaveButton?: boolean;
}

export default function ExtractedDataDisplay({ data, showSaveButton = false }: ExtractedDataDisplayProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [localSaveStatus, setLocalSaveStatus] = useState<{
    saved: boolean;
    error?: string;
    id?: string;
  }>({
    saved: data.saved || false,
    error: data.save_error,
    id: data.invoice_id
  });

  const copyToClipboard = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(String(text));
    toast.success('Copied to clipboard');
  };

  const formatCurrency = (amount: any, currencyCode: string = 'USD') => {
    if (amount === null || amount === undefined || amount === '') return '-';
    const num = Number(amount);
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
    return `${currencyCode || 'USD'} ${formatted}`;
  };

  const copyAll = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    toast.success('All data copied to clipboard');
  };

  const handleRetrySave = async () => {
    try {
      setIsSaving(true);
      const loadingToast = toast.loading('Retrying save to database...');
      const response = await saveInvoice(data);
      toast.dismiss(loadingToast);
      toast.success('Successfully saved to database!');
      setLocalSaveStatus({
        saved: true,
        id: response.invoice_id
      });
    } catch (err: any) {
      const msg = err.message || 'Failed to save invoice';
      toast.error(msg);
      setLocalSaveStatus(prev => ({ ...prev, error: msg }));
    } finally {
      setIsSaving(false);
    }
  };

  const CopyBtn = ({ text }: { text: string | number | null | undefined }) => {
    if (text === null || text === undefined || text === '') return null;
    return (
      <button 
        onClick={() => copyToClipboard(String(text))}
        className="ml-2 text-gray-400 hover:text-blue-500 transition-colors"
        title="Copy"
      >
        <Copy size={14} />
      </button>
    );
  };

  const FieldRow = ({ label, value }: { label: string, value: string | number | null | undefined }) => (
    <div className="flex justify-between items-start py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-500 font-medium text-sm w-1/3">{label}</span>
      <div className="w-2/3 flex justify-between items-center text-gray-900 text-sm">
        <span className="truncate max-w-[90%]">{value || '-'}</span>
        <CopyBtn text={value} />
      </div>
    </div>
  );

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold text-gray-800">Extracted Invoice Data</h2>
          
          {/* Save Status Badge */}
          {localSaveStatus.saved ? (
            <span className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full border border-green-200">
              <CheckCircle size={12} />
              <span>SAVED</span>
            </span>
          ) : localSaveStatus.error ? (
            <span className="flex items-center space-x-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-full border border-red-200">
              <AlertCircle size={12} />
              <span>SAVE FAILED</span>
            </span>
          ) : null}
        </div>

        <div className="flex space-x-3 w-full sm:w-auto">
          <button 
            onClick={copyAll}
            className="flex items-center justify-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium flex-1 sm:flex-initial"
          >
            <Copy size={16} />
            <span>Copy JSON</span>
          </button>
          
          {/* Show Retry button if failed, instead of always showing Save button */}
          {!localSaveStatus.saved && (
            <button 
              onClick={handleRetrySave}
              disabled={isSaving}
              className={`flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium shadow-sm flex-1 sm:flex-initial ${isSaving ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              {isSaving ? <RotateCw size={16} className="animate-spin" /> : <Save size={16} />}
              <span>{localSaveStatus.error ? 'Retry Save' : 'Save to Database'}</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Supplier Info */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Supplier Information</h3>
          <FieldRow label="Name" value={data.supplier?.name} />
          <FieldRow label="Address" value={data.supplier?.address} />
          <FieldRow label="Email" value={data.supplier?.email} />
          <FieldRow label="Phone" value={data.supplier?.phone} />
          <FieldRow label="Tax ID" value={data.supplier?.tax_id} />
        </div>

        {/* Invoice Info */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Invoice Details</h3>
          <FieldRow label="Invoice Number" value={data.invoice_info?.invoice_number} />
          <FieldRow label="Date" value={data.invoice_info?.invoice_date} />
          <FieldRow label="Due Date" value={data.invoice_info?.due_date} />
          <FieldRow label="Currency" value={data.invoice_info?.currency} />
          <FieldRow label="Payment Terms" value={data.invoice_info?.payment_terms} />
          <FieldRow label="PO Number" value={data.invoice_info?.purchase_order} />
        </div>

        {/* Bill To */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Bill To</h3>
          <FieldRow label="Company" value={data.bill_to?.company_name} />
          <FieldRow label="Address" value={data.bill_to?.address_line} />
          <FieldRow label="City" value={data.bill_to?.city} />
          <FieldRow label="State" value={data.bill_to?.state} />
          <FieldRow label="ZIP Code" value={data.bill_to?.zip_code} />
          <FieldRow label="Country" value={data.bill_to?.country} />
        </div>

        {/* Ship To (If exists) */}
        {(data.ship_to && Object.values(data.ship_to).some(v => v)) && (
          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Ship To</h3>
            <FieldRow label="Company" value={data.ship_to?.company_name} />
            <FieldRow label="Address" value={data.ship_to?.address_line} />
            <FieldRow label="City" value={data.ship_to?.city} />
            <FieldRow label="State" value={data.ship_to?.state} />
            <FieldRow label="ZIP Code" value={data.ship_to?.zip_code} />
            <FieldRow label="Country" value={data.ship_to?.country} />
          </div>
        )}
      </div>

      {/* Line Items Table */}
      <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
        <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Line Items</h3>
        <table className="w-full text-sm text-left text-gray-500">
          <thead className="text-xs text-gray-700 uppercase bg-gray-50">
            <tr>
              <th className="px-4 py-3 rounded-l-lg">Description</th>
              <th className="px-4 py-3">Code</th>
              <th className="px-4 py-3">Qty</th>
              <th className="px-4 py-3">Unit</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3 rounded-r-lg">Total</th>
            </tr>
          </thead>
          <tbody>
            {(data.line_items || []).map((item: any, idx: number) => (
              <tr key={idx} className="bg-white border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{item.description || '-'}</td>
                <td className="px-4 py-3">{item.item_code || '-'}</td>
                <td className="px-4 py-3">{item.quantity}</td>
                <td className="px-4 py-3">{item.unit || '-'}</td>
                <td className="px-4 py-3">{formatCurrency(item.unit_price, data.invoice_info?.currency)}</td>
                <td className="px-4 py-3 font-semibold">{formatCurrency(item.total_price, data.invoice_info?.currency)}</td>
              </tr>
            ))}
            {(!data.line_items || data.line_items.length === 0) && (
              <tr>
                <td colSpan={6} className="px-4 py-4 text-center text-gray-500">No line items found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
         {/* Notes */}
         <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Notes</h3>
          <p className="text-gray-600 text-sm whitespace-pre-wrap">{data.notes || 'No notes found.'}</p>
        </div>

        {/* Totals */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-base font-semibold text-gray-800 mb-4 border-b pb-2">Totals</h3>
          <FieldRow label="Subtotal" value={formatCurrency(data.totals?.subtotal, data.invoice_info?.currency)} />
          <FieldRow label="Tax Amount" value={formatCurrency(data.totals?.tax_amount, data.invoice_info?.currency)} />
          <FieldRow label="Discount" value={formatCurrency(data.totals?.discount, data.invoice_info?.currency)} />
          
          <div className="flex justify-between items-center py-4 mt-2 border-t-2 border-gray-100">
            <span className="text-gray-800 font-bold text-lg">Total Amount</span>
            <div className="flex items-center">
              <span className="text-blue-600 font-bold text-2xl">
                 {formatCurrency(data.totals?.total_amount, data.invoice_info?.currency)}
              </span>
              <CopyBtn text={data.totals?.total_amount} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
