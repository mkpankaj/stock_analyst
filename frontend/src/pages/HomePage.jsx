import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { analysisAPI } from '../api';

export default function HomePage() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [analysisDates, setAnalysisDates] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadLatestAnalysis();
    loadAnalysisDates();
  }, []);

  useEffect(() => {
    if (analyzing) {
      const interval = setInterval(checkAnalysisStatus, 1000);
      return () => clearInterval(interval);
    }
  }, [analyzing]);

  const loadLatestAnalysis = async () => {
    try {
      const response = await analysisAPI.getLatest();
      setAnalysis(response.data);
    } catch (err) {
      console.error('Failed to load analysis', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysisDates = async () => {
    try {
      const response = await analysisAPI.getDates();
      setAnalysisDates(response.data.dates);
    } catch (err) {
      console.error('Failed to load dates', err);
    }
  };

  const checkAnalysisStatus = async () => {
    try {
      const response = await analysisAPI.getStatus();
      if (response.data.status === 'completed') {
        await loadLatestAnalysis();
        setAnalyzing(false);
      }
    } catch (err) {
      console.error('Error checking status', err);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await analysisAPI.trigger();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to trigger analysis');
      setAnalyzing(false);
    }
  };

  const handleLoadDate = async (date) => {
    setSelectedDate(date);
    try {
      const response = await analysisAPI.getByDate(date);
      setAnalysis(response.data);
    } catch (err) {
      alert('Failed to load analysis for date');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  const canAnalyze = !analyzing;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Stock Analyst</h1>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/config')}
                className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Configuration
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-gray-900">Analysis</h2>
            <div className="flex gap-2">
              <button
                onClick={handleAnalyze}
                disabled={!canAnalyze}
                className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {analyzing ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </div>

          {analysisDates.length > 0 && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Load Previous Analysis
              </label>
              <select
                onChange={(e) => e.target.value && handleLoadDate(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2"
              >
                <option value="">Select a date...</option>
                {analysisDates.map((date) => (
                  <option key={date} value={date}>
                    {new Date(date).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div>
          )}

          {analyzing && (
            <div className="mb-4 p-4 bg-blue-50 rounded-md">
              <p className="text-sm text-blue-800">Analysis in progress...</p>
            </div>
          )}
        </div>

        {analysis && (analysis.gainers.length > 0 || analysis.losers.length > 0) ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 bg-green-50 border-b">
                <h3 className="text-lg font-bold text-green-900">Top 10 Gainers</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Rank</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Ticker</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Change %</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.gainers.map((stock) => (
                      <tr key={stock.ticker} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/stock/${stock.ticker}`)}>
                        <td className="px-4 py-2 text-sm">{stock.rank}</td>
                        <td className="px-4 py-2 text-sm font-medium">{stock.ticker}</td>
                        <td className="px-4 py-2 text-sm text-green-600 font-semibold">
                          +{stock.price_change_pct.toFixed(2)}%
                        </td>
                        <td className="px-4 py-2 text-sm">{stock.trend_label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 bg-red-50 border-b">
                <h3 className="text-lg font-bold text-red-900">Top 10 Losers</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Rank</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Ticker</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Change %</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.losers.map((stock) => (
                      <tr key={stock.ticker} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/stock/${stock.ticker}`)}>
                        <td className="px-4 py-2 text-sm">{stock.rank}</td>
                        <td className="px-4 py-2 text-sm font-medium">{stock.ticker}</td>
                        <td className="px-4 py-2 text-sm text-red-600 font-semibold">
                          {stock.price_change_pct.toFixed(2)}%
                        </td>
                        <td className="px-4 py-2 text-sm">{stock.trend_label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <p className="text-gray-600">
              {analyzing ? 'Analyzing...' : 'No analysis yet. Click Analyze to get started.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
