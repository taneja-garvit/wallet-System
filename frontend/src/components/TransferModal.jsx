import { useState, useEffect } from 'react';
import { transferMoney } from '../api/api';

const TransferModal = ({ onClose, onSuccess, wallets }) => {
  const [receiverId, setReceiverId] = useState('');
  const [amount, setAmount] = useState('');
  const [sourceCurrency, setSourceCurrency] = useState('');
  const [targetCurrency, setTargetCurrency] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const CURRENCY_SYMBOLS = {
    USD: '$',
    INR: '₹',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
    AUD: 'A$'
  };

  const FX_RATES = {
    'USD-INR': 83.0, 'USD-EUR': 0.92, 'USD-GBP': 0.79, 'USD-JPY': 149.5, 'USD-AUD': 1.52,
    'EUR-USD': 1.087, 'EUR-INR': 90.2, 'EUR-GBP': 0.86, 'EUR-JPY': 162.5, 'EUR-AUD': 1.65,
    'GBP-USD': 1.266, 'GBP-INR': 105.0, 'GBP-EUR': 1.163, 'GBP-JPY': 189.2, 'GBP-AUD': 1.92,
    'INR-USD': 0.012048, 'JPY-USD': 0.00669, 'AUD-USD': 0.658
  };

  useEffect(() => {
    if (wallets.length > 0 && !sourceCurrency) {
      setSourceCurrency(wallets[0].currency);
      setTargetCurrency(wallets[0].currency);
    }
  }, [wallets]);

  const getCurrentBalance = () => {
    const wallet = wallets.find(w => w.currency === sourceCurrency);
    return wallet ? wallet.balance : 0;
  };

  const getConvertedAmount = () => {
    if (!amount || !sourceCurrency || !targetCurrency) return 0;
    if (sourceCurrency === targetCurrency) return parseFloat(amount);
    
    const rateKey = `${sourceCurrency}-${targetCurrency}`;
    const rate = FX_RATES[rateKey] || 1.0;
    return (parseFloat(amount) * rate).toFixed(2);
  };

  const getFXRate = () => {
    if (sourceCurrency === targetCurrency) return 1.0;
    const rateKey = `${sourceCurrency}-${targetCurrency}`;
    return FX_RATES[rateKey] || 1.0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    const amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    const currentBalance = getCurrentBalance();
    if (amountNum > currentBalance) {
      setError(`Insufficient balance in ${sourceCurrency} wallet`);
      return;
    }

    if (!receiverId || isNaN(parseInt(receiverId))) {
      setError('Please enter a valid receiver ID');
      return;
    }

    if (!sourceCurrency || !targetCurrency) {
      setError('Please select currencies');
      return;
    }

    setLoading(true);

    try {
      const result = await transferMoney(
        parseInt(receiverId),
        sourceCurrency,
        targetCurrency,
        amountNum
      );
      
      if (result.status === 'SUCCESS') {
        const convertedAmt = result.target_amount;
        setSuccess(
          `✅ Sent ${CURRENCY_SYMBOLS[sourceCurrency]}${amountNum.toFixed(2)} → ` +
          `Receiver gets ${CURRENCY_SYMBOLS[targetCurrency]}${convertedAmt.toFixed(2)}`
        );
        setTimeout(() => {
          onSuccess();
        }, 2000);
      } else if (result.status === 'FAILED') {
        setError(result.error || 'Transfer failed');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Transfer failed';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 px-4 animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-8 relative transform transition-all animate-slideUp">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl p-2 transition"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex items-center space-x-3 mb-6">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </div>
          <div>
            <h3 className="text-2xl font-bold text-gray-900">Send Money</h3>
            <p className="text-sm text-gray-600">Transfer with instant FX conversion</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-green-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-green-700 text-sm font-medium">{success}</p>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="receiverId" className="block text-sm font-semibold text-gray-700 mb-2">
              Receiver User ID
            </label>
            <input
              id="receiverId"
              type="number"
              required
              value={receiverId}
              onChange={(e) => setReceiverId(e.target.value)}
              className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all"
              placeholder="Enter recipient's user ID"
              disabled={loading}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="sourceCurrency" className="block text-sm font-semibold text-gray-700 mb-2">
                From
              </label>
              <select
                id="sourceCurrency"
                value={sourceCurrency}
                onChange={(e) => setSourceCurrency(e.target.value)}
                className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all font-medium"
                disabled={loading}
                required
              >
                {wallets.map(wallet => (
                  <option key={wallet.wallet_id} value={wallet.currency}>
                    {CURRENCY_SYMBOLS[wallet.currency]} {wallet.currency} ({wallet.balance.toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="targetCurrency" className="block text-sm font-semibold text-gray-700 mb-2">
                To
              </label>
              <select
                id="targetCurrency"
                value={targetCurrency}
                onChange={(e) => setTargetCurrency(e.target.value)}
                className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all font-medium"
                disabled={loading}
                required
              >
                <option value="USD">{CURRENCY_SYMBOLS.USD} USD</option>
                <option value="INR">{CURRENCY_SYMBOLS.INR} INR</option>
                <option value="EUR">{CURRENCY_SYMBOLS.EUR} EUR</option>
                <option value="GBP">{CURRENCY_SYMBOLS.GBP} GBP</option>
                <option value="JPY">{CURRENCY_SYMBOLS.JPY} JPY</option>
                <option value="AUD">{CURRENCY_SYMBOLS.AUD} AUD</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="amount" className="block text-sm font-semibold text-gray-700 mb-2">
              Amount
            </label>
            <div className="relative">
              <input
                id="amount"
                type="number"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all text-lg font-semibold"
                placeholder="0.00"
                disabled={loading}
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">
                {sourceCurrency}
              </div>
            </div>
            <p className="mt-2 text-xs text-gray-600 flex items-center justify-between">
              <span>Available balance</span>
              <span className="font-semibold text-violet-600">
                {CURRENCY_SYMBOLS[sourceCurrency]}{getCurrentBalance().toFixed(2)}
              </span>
            </p>
          </div>

          {/* FX Conversion Preview */}
          {amount && sourceCurrency !== targetCurrency && (
            <div className="bg-gradient-to-br from-violet-50 to-indigo-50 border-2 border-violet-200 rounded-2xl p-5">
              <div className="flex items-center space-x-2 mb-3">
                <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
                <p className="text-sm font-bold text-violet-900">Currency Conversion</p>
              </div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-bold text-gray-900">
                    {CURRENCY_SYMBOLS[sourceCurrency]}{parseFloat(amount).toFixed(2)}
                  </span>
                  <span className="text-sm text-gray-600 font-medium">{sourceCurrency}</span>
                </div>
                <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-bold text-violet-600">
                    {CURRENCY_SYMBOLS[targetCurrency]}{getConvertedAmount()}
                  </span>
                  <span className="text-sm text-gray-600 font-medium">{targetCurrency}</span>
                </div>
              </div>
              <div className="bg-white bg-opacity-60 rounded-lg px-3 py-2">
                <p className="text-xs text-gray-700">
                  Exchange rate: <span className="font-bold text-violet-700">1 {sourceCurrency} = {getFXRate()} {targetCurrency}</span>
                </p>
              </div>
            </div>
          )}

          <div className="pt-2 flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-6 py-3.5 border-2 border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50 transition-all disabled:opacity-50 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl hover:from-violet-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </span>
              ) : (
                'Send Money'
              )}
            </button>
          </div>
        </form>

        <div className="mt-6 p-4 bg-gradient-to-r from-violet-50 to-indigo-50 rounded-xl border border-violet-100">
          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-violet-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <div className="text-xs text-violet-900">
              <p className="font-semibold mb-1">Secure & Instant</p>
              <p className="text-violet-700">Protected by bank-grade encryption. Auto-generated unique ID prevents duplicates.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransferModal;

