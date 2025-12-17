import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import './Charts.css';


const COLORS = {
  primary: '#10b981',
  secondary: '#3b82f6',
  warning: '#f59e0b',
  error: '#ef4444',
  purple: '#8b5cf6',
  pink: '#ec4899',
  cyan: '#06b6d4',
};

const CHART_COLORS = [
  COLORS.primary,
  COLORS.secondary,
  COLORS.warning,
  COLORS.purple,
  COLORS.pink,
  COLORS.cyan,
];


export const TrendLineChart = ({
  data,
  lines = [{ key: 'value', color: COLORS.primary, name: 'Value' }],
  xAxisKey = 'date',
  height = 300,
  showGrid = true,
  showLegend = true,
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">No data available</div>;
  }

  return (
    <div className="chart-wrapper" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" />}
          <XAxis 
            dataKey={xAxisKey} 
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          />
          <YAxis 
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{
              background: 'var(--card-bg)',
              border: '1px solid var(--border-primary)',
              borderRadius: '8px',
            }}
          />
          {showLegend && <Legend />}
          {lines.map((line, index) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.name}
              stroke={line.color || CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};


export const ComparisonBarChart = ({
  data,
  bars = [{ key: 'value', color: COLORS.primary, name: 'Value' }],
  xAxisKey = 'name',
  height = 300,
  layout = 'vertical',
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">No data available</div>;
  }

  const isHorizontal = layout === 'horizontal';

  return (
    <div className="chart-wrapper" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart 
          data={data} 
          layout={layout}
          margin={{ top: 10, right: 30, left: isHorizontal ? 0 : 80, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" />
          {isHorizontal ? (
            <>
              <XAxis dataKey={xAxisKey} stroke="var(--text-secondary)" />
              <YAxis stroke="var(--text-secondary)" />
            </>
          ) : (
            <>
              <XAxis type="number" stroke="var(--text-secondary)" />
              <YAxis dataKey={xAxisKey} type="category" stroke="var(--text-secondary)" width={80} />
            </>
          )}
          <Tooltip 
            contentStyle={{
              background: 'var(--card-bg)',
              border: '1px solid var(--border-primary)',
              borderRadius: '8px',
            }}
          />
          <Legend />
          {bars.map((bar, index) => (
            <Bar
              key={bar.key}
              dataKey={bar.key}
              name={bar.name}
              fill={bar.color || CHART_COLORS[index % CHART_COLORS.length]}
              radius={[4, 4, 4, 4]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};


export const DistributionPieChart = ({
  data,
  dataKey = 'value',
  nameKey = 'name',
  height = 300,
  showLabel = true,
  innerRadius = 0,
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">No data available</div>;
  }

  return (
    <div className="chart-wrapper" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey={dataKey}
            nameKey={nameKey}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius="80%"
            label={showLabel ? ({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%` : false}
            labelLine={showLabel}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color || CHART_COLORS[index % CHART_COLORS.length]} 
              />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{
              background: 'var(--card-bg)',
              border: '1px solid var(--border-primary)',
              borderRadius: '8px',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};


export const StatsCard = ({ title, value, change, icon, trend = 'neutral' }) => {
  const trendColors = {
    up: 'var(--color-success)',
    down: 'var(--color-error)',
    neutral: 'var(--text-secondary)',
  };

  return (
    <div className="stats-card">
      {icon && <span className="stats-icon">{icon}</span>}
      <div className="stats-content">
        <span className="stats-title">{title}</span>
        <span className="stats-value">{value}</span>
        {change && (
          <span className="stats-change" style={{ color: trendColors[trend] }}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {change}
          </span>
        )}
      </div>
    </div>
  );
};

export default {
  TrendLineChart,
  ComparisonBarChart,
  DistributionPieChart,
  StatsCard,
};
