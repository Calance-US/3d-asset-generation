import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Grid, CircularProgress, Alert, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import { BASE_URL } from '../../lib/utils';

const ValidationMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchValidationMetrics();
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

  // Extract and fallback for all relevant fields
  const system_health = metrics.system_health || {};
  const validation_performance = metrics.validation_performance || {};
  const quality_distribution = metrics.quality_distribution || {};
  const provider_performance = metrics.provider_performance || [];
  const phase_error_distribution = metrics.phase_error_distribution || [];

  // System Health
  const overallSuccessRate = system_health.overall_success_rate ?? 0;
  const averageQualityScore = system_health.average_quality_score ?? 0;
  const improvementRate = system_health.improvement_rate ?? 0;
  const totalValidations = system_health.total_validations ?? 0;

  // Validation Performance
  const totalValidationErrors = validation_performance.total_validation_errors ?? 0;
  const uniquePromptsValidated = validation_performance.unique_prompts_validated ?? 0;
  const successRate = validation_performance.success_rate ?? 0;
  const avgAttemptsPerPrompt = validation_performance.avg_attempts_per_prompt ?? 0;
  const attemptBreakdown = validation_performance.attempt_breakdown || [];

  // Quality Distribution
  const averageScore = quality_distribution.average_score ?? 0;
  const minScore = quality_distribution.min_score ?? 0;
  const maxScore = quality_distribution.max_score ?? 0;
  const scoreImprovementTrend = quality_distribution.score_improvement_trend || [];

  return (
    <div className="space-y-6">
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
        Validation System Metrics
      </Typography>

      {/* System Health Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>System Health</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}><b>Overall Success Rate:</b> {overallSuccessRate.toFixed(1)}%</Grid>
            <Grid item xs={6} md={3}><b>Average Quality Score:</b> {averageQualityScore.toFixed(1)}</Grid>
            <Grid item xs={6} md={3}><b>Improvement Rate:</b> {improvementRate.toFixed(1)}%</Grid>
            <Grid item xs={6} md={3}><b>Total Validations:</b> {totalValidations}</Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Validation Performance */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Validation Performance</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}><b>Total Validation Errors:</b> {totalValidationErrors}</Grid>
            <Grid item xs={6} md={3}><b>Unique Prompts Validated:</b> {uniquePromptsValidated}</Grid>
            <Grid item xs={6} md={3}><b>Success Rate:</b> {successRate.toFixed(1)}%</Grid>
            <Grid item xs={6} md={3}><b>Avg Attempts/Prompt:</b> {avgAttemptsPerPrompt.toFixed(2)}</Grid>
          </Grid>
          <Box mt={2}>
            <Typography variant="subtitle1">Attempt Breakdown</Typography>
            <TableContainer component={Paper} sx={{ mt: 1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Attempt</TableCell>
                    <TableCell>Total Attempts</TableCell>
                    <TableCell>Critical Errors</TableCell>
                    <TableCell>Avg Quality Score</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {attemptBreakdown.length > 0 ? attemptBreakdown.map((row, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{row.attempt}</TableCell>
                      <TableCell>{row.total_attempts}</TableCell>
                      <TableCell>{row.critical_errors}</TableCell>
                      <TableCell>{row.avg_quality_score.toFixed(2)}</TableCell>
                    </TableRow>
                  )) : (
                    <TableRow><TableCell colSpan={4}>No attempt breakdown data.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </CardContent>
      </Card>

      {/* Quality Distribution */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Quality Distribution</Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}><b>Average Score:</b> {averageScore.toFixed(2)}</Grid>
            <Grid item xs={4}><b>Min Score:</b> {minScore.toFixed(2)}</Grid>
            <Grid item xs={4}><b>Max Score:</b> {maxScore.toFixed(2)}</Grid>
          </Grid>
          <Box mt={2}>
            <Typography variant="subtitle1">Score Improvement Trend</Typography>
            <TableContainer component={Paper} sx={{ mt: 1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Attempt</TableCell>
                    <TableCell>Avg Score</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scoreImprovementTrend.length > 0 ? scoreImprovementTrend.map((row, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{row.attempt}</TableCell>
                      <TableCell>{row.avg_score.toFixed(2)}</TableCell>
                    </TableRow>
                  )) : (
                    <TableRow><TableCell colSpan={2}>No score improvement data.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </CardContent>
      </Card>

      {/* Provider Performance */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Provider Performance</Typography>
          <TableContainer component={Paper} sx={{ mt: 1 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Provider</TableCell>
                  <TableCell>Total Errors</TableCell>
                  <TableCell>Avg Quality</TableCell>
                  <TableCell>Unique Prompts</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {provider_performance.length > 0 ? provider_performance.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{row.provider}</TableCell>
                    <TableCell>{row.total_errors}</TableCell>
                    <TableCell>{row.avg_quality.toFixed(2)}</TableCell>
                    <TableCell>{row.unique_prompts}</TableCell>
                  </TableRow>
                )) : (
                  <TableRow><TableCell colSpan={4}>No provider performance data.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Phase Error Distribution */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Phase Error Distribution</Typography>
          <TableContainer component={Paper} sx={{ mt: 1 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Phase</TableCell>
                  <TableCell>Total Errors</TableCell>
                  <TableCell>Critical Errors</TableCell>
                  <TableCell>Error Rate (%)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {phase_error_distribution.length > 0 ? phase_error_distribution.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{row.phase}</TableCell>
                    <TableCell>{row.total_errors}</TableCell>
                    <TableCell>{row.critical_errors}</TableCell>
                    <TableCell>{row.error_rate.toFixed(1)}%</TableCell>
                  </TableRow>
                )) : (
                  <TableRow><TableCell colSpan={4}>No phase error distribution data.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
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
