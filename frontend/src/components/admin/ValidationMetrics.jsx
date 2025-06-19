import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Grid, CircularProgress, Alert, Box, LinearProgress, Chip } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { BASE_URL } from '../../lib/utils';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1'];

const ValidationMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchValidationMetrics();
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(fetchValidationMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchValidationMetrics = async () => {
    try {
      const response = await fetch(`${BASE_URL}/admin/validation-metrics`);
      if (!response.ok) {
        throw new Error('Failed to fetch validation metrics');
      }
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading validation metrics: {error}
      </Alert>
    );
  }

  if (!metrics) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No validation metrics available
      </Alert>
    );
  }

  const { validation_performance, quality_distribution, feedback_effectiveness, system_health } = metrics;

  // Prepare data for charts
  const phasePerformanceData = Object.entries(validation_performance?.phase_performance || {}).map(([phase, data]) => ({
    phase: phase.replace('_', '/').toUpperCase(),
    successRate: (data.success_rate * 100).toFixed(1),
    avgTime: data.avg_time.toFixed(2),
    count: data.count
  }));

  const qualityTierData = Object.entries(quality_distribution?.tier_distribution || {}).map(([tier, count]) => ({
    name: tier.charAt(0).toUpperCase() + tier.slice(1),
    value: count,
    color: tier === 'premium' ? '#8884d8' : tier === 'standard' ? '#82ca9d' : tier === 'basic' ? '#ffc658' : '#ff7300'
  }));

  const getTrendColor = (value) => {
    if (value >= 0.8) return 'success';
    if (value >= 0.6) return 'warning';
    return 'error';
  };

  const getQualityColor = (score) => {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    return 'error';
  };

  return (
    <div className="space-y-6">
      <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#fff', fontWeight: 'bold' }}>
        Validation System Metrics
      </Typography>

      {/* System Health Overview */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography color="#9ca3af" gutterBottom>
                Overall Success Rate
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="h4" component="div" color={getTrendColor(system_health?.overall_success_rate || 0)}>
                  {((system_health?.overall_success_rate || 0) * 100).toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(system_health?.overall_success_rate || 0) * 100}
                  sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                  color={getTrendColor(system_health?.overall_success_rate || 0)}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography color="#9ca3af" gutterBottom>
                Average Quality Score
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="h4" component="div" color={getQualityColor(system_health?.average_quality_score || 0)}>
                  {(system_health?.average_quality_score || 0).toFixed(1)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(system_health?.average_quality_score || 0) * 10}
                  sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                  color={getQualityColor(system_health?.average_quality_score || 0)}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography color="#9ca3af" gutterBottom>
                Improvement Rate
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="h4" component="div" color={getTrendColor(system_health?.improvement_rate || 0)}>
                  {((system_health?.improvement_rate || 0) * 100).toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(system_health?.improvement_rate || 0) * 100}
                  sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                  color={getTrendColor(system_health?.improvement_rate || 0)}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Validation Performance Stats */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Phase Performance
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={phasePerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="phase" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#374151', border: 'none', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Bar dataKey="successRate" fill="#8884d8" name="Success Rate (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quality Distribution
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={qualityTierData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {qualityTierData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#374151', border: 'none', borderRadius: '8px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Performance Metrics */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Details
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="#9ca3af">Total Validations:</Typography>
                  <Typography>{validation_performance?.total_validations || 0}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="#9ca3af">Successful Validations:</Typography>
                  <Typography>{validation_performance?.successful_validations || 0}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="#9ca3af">Average Validation Time:</Typography>
                  <Typography>{(validation_performance?.average_validation_time || 0).toFixed(2)}s</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Feedback Loop Effectiveness
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="#9ca3af">Learning Updates:</Typography>
                  <Typography>{feedback_effectiveness?.learning_updates || 0}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="#9ca3af">Pattern Recognition:</Typography>
                  <Typography>{feedback_effectiveness?.patterns_identified || 0}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="#9ca3af">Adaptation Success:</Typography>
                  <Typography>{((feedback_effectiveness?.adaptation_success_rate || 0) * 100).toFixed(1)}%</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Phase-Specific Details */}
      <Card sx={{ bgcolor: '#1f2937', color: '#fff' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Phase-Specific Performance
          </Typography>
          <Grid container spacing={2}>
            {phasePerformanceData.map((phase) => (
              <Grid item xs={12} sm={6} md={3} key={phase.phase}>
                <Box
                  p={2}
                  bgcolor="#374151"
                  borderRadius={1}
                  display="flex"
                  flexDirection="column"
                  gap={1}
                >
                  <Typography variant="subtitle1" fontWeight="bold">
                    {phase.phase}
                  </Typography>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="#9ca3af">Success Rate:</Typography>
                    <Chip
                      label={`${phase.successRate}%`}
                      size="small"
                      color={parseFloat(phase.successRate) >= 80 ? 'success' : parseFloat(phase.successRate) >= 60 ? 'warning' : 'error'}
                    />
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="#9ca3af">Avg Time:</Typography>
                    <Typography variant="body2">{phase.avgTime}s</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="#9ca3af">Count:</Typography>
                    <Typography variant="body2">{phase.count}</Typography>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Refresh Info */}
      <Box display="flex" justifyContent="center">
        <Typography variant="body2" color="#9ca3af">
          Metrics refresh automatically every 30 seconds
        </Typography>
      </Box>
    </div>
  );
};

export default ValidationMetrics;
