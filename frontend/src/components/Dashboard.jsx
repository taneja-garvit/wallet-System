import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getWallets, createWallet } from '../api/api';
import TransferModal from './TransferModal';
import TransactionHistory from './TransactionHistory';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [wallets, setWallets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showCreateWallet, setShowCreateWallet] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [refreshKey, setRefreshKey] = useState(0);
  const [createError, setCreateError] = useState('');

  const SUPPORTED_CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD'];
  const CURRENCY_SYMBOLS = {
    USD: '$',
    INR: '₹',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
    AUD: 'A$'
  };

  useEffect(() => {
    loadWallets();
  }, [refreshKey]);

  const loadWallets = async () => {
    try {
      setLoading(true);
      const data = await getWallets();
      setWallets(data.wallets || []);
    } catch (error) {
      console.error('Failed to load wallets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWallet = async () => {
    setCreateError('');
    try {
      await createWallet(selectedCurrency);
      setShowCreateWallet(false);
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to create wallet';
      setCreateError(errorMsg);
    }
  };

  const handleTransferSuccess = () => {
    setRefreshKey(prev => prev + 1); // Refresh wallet and transactions
    setShowTransferModal(false);
  };

  const getAvailableCurrencies = () => {
    const existingCurrencies = wallets.map(w => w.currency);
    return SUPPORTED_CURRENCIES.filter(c => !existingCurrencies.includes(c));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 backdrop-blur-lg bg-opacity-80 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Wallet</h1>
                <p className="text-xs text-gray-500">Multi-Currency</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right bg-gradient-to-r from-violet-50 to-indigo-50 px-4 py-2 rounded-xl border border-violet-100">
                <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                <p className="text-xs text-violet-600 font-semibold">ID: {user?.id}</p>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all border border-gray-200"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Multi-Currency Wallets Grid */}
        <div className="mb-10">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Your Wallets</h2>
              <p className="text-sm text-gray-600 mt-1">Manage balances across multiple currencies</p>
            </div>
            <button
              onClick={() => setShowCreateWallet(true)}
              className="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl hover:from-violet-700 hover:to-indigo-700 transition-all font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Add Wallet</span>
            </button>
          </div>

          {wallets.length === 0 ? (
            <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-16 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-violet-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No wallets yet</h3>
              <p className="text-gray-600 mb-6">Create your first wallet to start managing your finances</p>
              <button
                onClick={() => setShowCreateWallet(true)}
                className="px-8 py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl hover:from-violet-700 hover:to-indigo-700 transition-all font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Create Your First Wallet
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {wallets.map((wallet, index) => {
                const gradients = [
                  'from-violet-500 to-purple-600',
                  'from-blue-500 to-cyan-600',
                  'from-emerald-500 to-teal-600',
                  'from-orange-500 to-pink-600',
                  'from-rose-500 to-red-600',
                  'from-indigo-500 to-blue-600'
                ];
                const gradient = gradients[index % gradients.length];
                
                return (
                  <div
                    key={wallet.wallet_id}
                    className={`bg-gradient-to-br ${gradient} rounded-3xl shadow-xl hover:shadow-2xl p-8 text-white transform hover:scale-105 transition-all duration-300 relative overflow-hidden group`}
                  >
                    {/* Background pattern */}
                    <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-5 transition-opacity"></div>
                    
                    <div className="relative">
                      <div className="flex justify-between items-start mb-6">
                        <div className="w-14 h-14 bg-white bg-opacity-20 backdrop-blur-sm rounded-2xl flex items-center justify-center text-3xl font-bold shadow-lg">
                          {CURRENCY_SYMBOLS[wallet.currency]}
                        </div>
                        <span className="bg-white bg-opacity-25 backdrop-blur-sm px-4 py-1.5 rounded-full text-sm font-bold shadow-lg">
                          {wallet.currency}
                        </span>
                      </div>
                      <div className="space-y-1 mb-4">
                        <p className="text-white text-opacity-80 text-xs font-medium uppercase tracking-wide">Available Balance</p>
                        <h3 className="text-4xl font-bold tracking-tight">
                          {CURRENCY_SYMBOLS[wallet.currency]}{wallet.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </h3>
                      </div>
                      <div className="flex items-center justify-between text-xs text-white text-opacity-70">
                        <span>ID #{wallet.wallet_id}</span>
                        <span className="flex items-center space-x-1">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Secured</span>
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {wallets.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
            <button
              onClick={() => setShowTransferModal(true)}
              className="group bg-white border-2 border-gray-200 hover:border-violet-300 px-8 py-6 rounded-2xl font-semibold hover:bg-gradient-to-r hover:from-violet-50 hover:to-indigo-50 transition-all shadow-lg hover:shadow-xl flex items-center justify-center space-x-3"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
              <div className="text-left">
                <p className="text-gray-900 font-bold text-lg">Send Money</p>
                <p className="text-gray-500 text-sm">Transfer to any currency</p>
              </div>
            </button>
            
            <button
              onClick={() => setShowCreateWallet(true)}
              className="group bg-white border-2 border-gray-200 hover:border-indigo-300 px-8 py-6 rounded-2xl font-semibold hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 transition-all shadow-lg hover:shadow-xl flex items-center justify-center space-x-3"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div className="text-left">
                <p className="text-gray-900 font-bold text-lg">Add Wallet</p>
                <p className="text-gray-500 text-sm">Create new currency</p>
              </div>
            </button>
          </div>
        )}

        {/* Transaction History */}
        <TransactionHistory key={refreshKey} />
      </main>

      {/* Transfer Modal */}
      {showTransferModal && (
        <TransferModal
          onClose={() => setShowTransferModal(false)}
          onSuccess={handleTransferSuccess}
          wallets={wallets}
        />
      )}

      {/* Create Wallet Modal */}
      {showCreateWallet && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 px-4 animate-fadeIn">
          <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-8 relative transform transition-all animate-slideUp">
            <button
              onClick={() => {
                setShowCreateWallet(false);
                setCreateError('');
              }}
              className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl p-2 transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="flex items-center space-x-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">Create New Wallet</h3>
                <p className="text-sm text-gray-600">Choose your currency</p>
              </div>
            </div>

            {createError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-red-700 text-sm">{createError}</p>
                </div>
              </div>
            )}

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Select Currency
              </label>
              <div className="grid grid-cols-2 gap-3">
                {getAvailableCurrencies().map(currency => (
                  <button
                    key={currency}
                    type="button"
                    onClick={() => setSelectedCurrency(currency)}
                    className={`p-4 border-2 rounded-xl transition-all ${
                      selectedCurrency === currency
                        ? 'border-violet-600 bg-gradient-to-br from-violet-50 to-indigo-50 shadow-lg'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="text-3xl mb-2">{CURRENCY_SYMBOLS[currency]}</div>
                    <div className="font-bold text-gray-900">{currency}</div>
                  </button>
                ))}
              </div>
              {getAvailableCurrencies().length === 0 && (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-600">
                    You have wallets in all supported currencies
                  </p>
                </div>
              )}
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowCreateWallet(false);
                  setCreateError('');
                }}
                className="flex-1 px-6 py-3.5 border-2 border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50 transition-all font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWallet}
                disabled={getAvailableCurrencies().length === 0}
                className="flex-1 px-6 py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl hover:from-violet-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg"
              >
                Create Wallet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

