import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { getInvoiceById } from '../services/api';
import ExtractedDataDisplay from '../components/ExtractedDataDisplay';

export default function InvoiceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchInvoice(id);
    }
  }, [id]);

  const fetchInvoice = async (invoiceId: string) => {
    try {
      const response = await getInvoiceById(invoiceId);
      
      // Remap the flat database response back into the grouped JSON structure expected by ExtractedDataDisplay
      const formattedData = {
        supplier: response.suppliers,
        invoice_info: {
          invoice_number: response.invoice_number,
          invoice_date: response.invoice_date,
          due_date: response.due_date,
          currency: response.currency,
          payment_terms: response.payment_terms,
          purchase_order: response.purchase_order
        },
        totals: {
          subtotal: response.subtotal,
          tax_amount: response.tax_amount,
          discount: response.discount,
          total_amount: response.total_amount
        },
        notes: response.notes,
        line_items: response.items || [],
        bill_to: response.addresses?.find((a: any) => a.address_type === 'bill_to') || null,
        ship_to: response.addresses?.find((a: any) => a.address_type === 'ship_to') || null,
      };
      
      setData(formattedData);
    } catch (err: any) {
      toast.error('Failed to load invoice details');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="animate-spin text-blue-500 mb-4" size={40} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 space-y-4">
        <h2 className="text-2xl font-bold text-gray-800">Invoice not found</h2>
        <button 
          onClick={() => navigate('/history')}
          className="text-blue-600 hover:underline"
        >
          Go back to history
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <button 
        onClick={() => navigate('/history')}
        className="flex items-center space-x-2 text-gray-500 hover:text-blue-600 transition-colors font-medium mb-4"
      >
        <ArrowLeft size={18} />
        <span>Back to History</span>
      </button>
      
      <ExtractedDataDisplay data={data} showSaveButton={false} />
    </div>
  );
}
