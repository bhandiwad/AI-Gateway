import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';

export default function UsageChart({ data, title = "Usage Over Time" }) {
  const formattedData = data?.map(item => ({
    ...item,
    date: new Date(item.timestamp).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    }),
    cost: Number(item.cost?.toFixed(4)) || 0,
    tokens: item.tokens || 0,
    requests: item.requests || 0,
  })) || [];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              stroke="#9ca3af"
              fontSize={12}
            />
            <YAxis 
              yAxisId="left"
              stroke="#9ca3af"
              fontSize={12}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              stroke="#9ca3af"
              fontSize={12}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="requests" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ fill: '#3b82f6' }}
              name="Requests"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="cost" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={{ fill: '#10b981' }}
              name="Cost ($)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
