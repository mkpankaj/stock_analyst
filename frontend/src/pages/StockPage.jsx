import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { stockAPI } from '../api';

export default function StockPage() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [chartData, setChartData] = useState([]);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStockData();
  }, [ticker]);

  const loadStockData = async () => {
    setLoading(true);
    setError('');
    try {
      const chartResponse = await stockAPI.getChart(ticker, 120);
      const formattedData = chartResponse.data.data.map(item => ({
        date: new Date(item.date).toLocaleDateString(),
        close: parseFloat(item.close.toFixed(2))
      }));
      setChartData(formattedData);

      const newsResponse = await stockAPI.getNews(ticker);
      setNews(newsResponse.data.news);
    } catch (err) {
      setError('Failed to load stock data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back
              </button>
              <h1 className="text-2xl font-bold text-gray-900">{ticker}</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="rounded-md bg-red-50 p-4 mb-4">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Price Trend (Weekly)</h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip formatter={(value) => `₹${value.toFixed(2)}`} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#2563eb"
                  dot={false}
                  name="Close Price"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-600">No price data available</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Latest News</h2>
          {news.length > 0 ? (
            <div className="space-y-4">
              {news.map((headline, idx) => (
                <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                  <p className="font-medium text-gray-900">{headline.headline}</p>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm text-gray-500">{headline.source}</span>
                    <a
                      href={headline.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Read →
                    </a>
                  </div>
                  {headline.published_at && (
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(headline.published_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No news available for this stock</p>
          )}
        </div>
      </div>
    </div>
  );
}
