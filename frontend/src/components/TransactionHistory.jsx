import { useState, useEffect } from 'react';
import { getTransactions } from '../api/api';

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const CURRENCY_SYMBOLS = {
    USD: '$',
    INR: '₹',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
    AUD: 'A$'
  };

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const data = await getTransactions(20);
      setTransactions(data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'SUCCESS':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h3 className="text-2xl font-bold text-gray-900">Recent Activity</h3>
          <p className="text-sm text-gray-600 mt-1">Your transaction history across all currencies</p>
        </div>
        <div className="w-10 h-10 bg-gradient-to-br from-violet-100 to-indigo-100 rounded-xl flex items-center justify-center">
          <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {transactions.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 bg-gradient-to-br from-violet-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-900 mb-1">No transactions yet</h4>
          <p className="text-sm text-gray-500">Your transaction history will appear here</p>
        </div>
      ) : (
        <div className="space-y-4">
          {transactions.map((tx) => {
            const isCrossCurrency = tx.source_currency !== tx.target_currency;
            const displayAmount = tx.type === 'CREDIT' ? tx.target_amount : tx.source_amount;
            const displayCurrency = tx.type === 'CREDIT' ? tx.target_currency : tx.source_currency;
            
            return (
              <div
                key={tx.id}
                className="border-2 border-gray-100 rounded-2xl hover:border-violet-200 hover:shadow-lg transition-all overflow-hidden bg-white group"
              >
                <div className="flex items-center justify-between p-5">
                  <div className="flex items-center space-x-4">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg ${
                      tx.type === 'CREDIT' 
                        ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
                        : 'bg-gradient-to-br from-violet-500 to-purple-600'
                    }`}>
                      {tx.type === 'CREDIT' ? (
                        <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                        </svg>
                      ) : (
                        <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                        </svg>
                      )}
                    </div>
                    
                    <div>
                      <div className="flex items-center space-x-2 mb-1">
                        <p className="font-bold text-gray-900 text-lg">
                          {tx.type === 'CREDIT' ? 'Received' : 'Sent'}
                        </p>
                        {isCrossCurrency && (
                          <span className="inline-flex items-center space-x-1 text-xs bg-gradient-to-r from-violet-100 to-purple-100 text-violet-700 px-2.5 py-1 rounded-full font-semibold">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                            </svg>
                            <span>FX</span>
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 font-medium">
                        {formatDate(tx.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className={`text-2xl font-bold mb-1 ${
                      tx.type === 'CREDIT' ? 'text-emerald-600' : 'text-violet-600'
                    }`}>
                      {tx.type === 'CREDIT' ? '+' : '-'}
                      {CURRENCY_SYMBOLS[displayCurrency]}
                      {displayAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <span className={`inline-block px-3 py-1 text-xs font-bold rounded-full ${getStatusColor(tx.status)}`}>
                      {tx.status}
                    </span>
                  </div>
                </div>

                {/* FX Details (for cross-currency transactions) */}
                {isCrossCurrency && (
                  <div className="bg-gradient-to-r from-violet-50 to-purple-50 px-5 py-4 border-t border-violet-100">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-2 text-gray-700">
                        <span className="font-semibold">{CURRENCY_SYMBOLS[tx.source_currency]}{tx.source_amount.toFixed(2)}</span>
                        <span className="text-gray-500">{tx.source_currency}</span>
                      </div>
                      <div className="flex items-center space-x-2 px-3 py-1.5 bg-white rounded-lg shadow-sm">
                        <svg className="w-4 h-4 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        <span className="font-bold text-violet-700 text-xs">
                          {tx.fx_rate}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-gray-700">
                        <span className="font-semibold">{CURRENCY_SYMBOLS[tx.target_currency]}{tx.target_amount.toFixed(2)}</span>
                        <span className="text-gray-500">{tx.target_currency}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TransactionHistory;

