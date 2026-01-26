import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getWallet, transferMoney, getTransactions } from '../api/api';
import TransferModal from './TransferModal';
import TransactionHistory from './TransactionHistory';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    loadWallet();
  }, [refreshKey]);

  const loadWallet = async () => {
    try {
      setLoading(true);
      const data = await getWallet();
      setWallet(data);
    } catch (error) {
      console.error('Failed to load wallet:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTransferSuccess = () => {
    setRefreshKey(prev => prev + 1); // Refresh wallet and transactions
    setShowTransferModal(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">💰</span>
            <h1 className="text-2xl font-bold text-gray-900">Wallet System</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Wallet Balance Card */}
        <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-xl p-8 text-white mb-8">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-blue-100 text-sm font-medium mb-2">Current Balance</p>
              <h2 className="text-5xl font-bold mb-4">
                ${wallet?.balance?.toFixed(2) || '0.00'}
              </h2>
              <p className="text-blue-100 text-sm">
                Wallet ID: #{wallet?.wallet_id}
              </p>
            </div>
            <button
              onClick={() => setShowTransferModal(true)}
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition shadow-lg transform hover:scale-105"
            >
              💸 Send Money
            </button>
          </div>
        </div>

        {/* Transaction History */}
        <TransactionHistory key={refreshKey} />
      </main>

      {/* Transfer Modal */}
      {showTransferModal && (
        <TransferModal
          onClose={() => setShowTransferModal(false)}
          onSuccess={handleTransferSuccess}
          currentBalance={wallet?.balance || 0}
        />
      )}
    </div>
  );
};

export default Dashboard;

