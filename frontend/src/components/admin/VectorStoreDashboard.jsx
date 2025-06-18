import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  CircularProgress,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import axios from 'axios';
import { BASE_URL } from '../../lib/utils';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const VectorStoreDashboard = () => {
  const [stats, setStats] = useState(null);
  const [vectors, setVectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    snippet_type: '',
    topic: '',
    education_level: '',
  });

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/admin/vector-store-stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching Vector Store stats:', error);
    }
  };

  const fetchVectors = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/admin/vector-store-vectors`, {
        params: {
          skip: (page - 1) * 10,
          limit: 10,
          ...filters,
        },
      });
      setVectors(response.data);
    } catch (error) {
      console.error('Error fetching Vector Store vectors:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchVectors();
  }, [page, filters]);

  const handleFilterChange = (field) => (event) => {
    setFilters(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    setPage(1);
  };

  const handlePageChange = (event, value) => {
    setPage(value);
  };

  if (!stats) {
    return <CircularProgress />;
  }

  const snippetTypeData = Object.entries(stats.snippet_types).map(([name, value]) => ({
    name,
    value,
  }));

  const topicData = Object.entries(stats.topics).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Vector Store Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Total Vectors</Typography>
              <Typography variant="h3">{stats.total_vectors}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Dimension</Typography>
              <Typography variant="h3">{stats.dimension}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Index Type</Typography>
              <Typography variant="h3">{stats.index_type}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Charts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Snippet Types Distribution</Typography>
              <PieChart width={400} height={300}>
                <Pie
                  data={snippetTypeData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label
                >
                  {snippetTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Topics Distribution</Typography>
              <BarChart width={400} height={300} data={topicData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </CardContent>
          </Card>
        </Grid>

        {/* Filters */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Snippet Type</InputLabel>
                    <Select
                      value={filters.snippet_type}
                      onChange={handleFilterChange('snippet_type')}
                    >
                      <MenuItem value="">All</MenuItem>
                      {Object.keys(stats.snippet_types).map(type => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Topic</InputLabel>
                    <Select
                      value={filters.topic}
                      onChange={handleFilterChange('topic')}
                    >
                      <MenuItem value="">All</MenuItem>
                      {Object.keys(stats.topics).map(topic => (
                        <MenuItem key={topic} value={topic}>
                          {topic}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Education Level</InputLabel>
                    <Select
                      value={filters.education_level}
                      onChange={handleFilterChange('education_level')}
                    >
                      <MenuItem value="">All</MenuItem>
                      {Object.keys(stats.education_levels).map(level => (
                        <MenuItem key={level} value={level}>
                          {level}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Vectors Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Vectors
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Snippet Type</TableCell>
                      <TableCell>Topic</TableCell>
                      <TableCell>Education Level</TableCell>
                      <TableCell>Summary</TableCell>
                      <TableCell>Filename</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {vectors.map(vector => (
                      <TableRow key={vector.id}>
                        <TableCell>{vector.id}</TableCell>
                        <TableCell>{vector.snippet_type}</TableCell>
                        <TableCell>{vector.topic}</TableCell>
                        <TableCell>{vector.education_level}</TableCell>
                        <TableCell>{vector.summary}</TableCell>
                        <TableCell>{vector.filename}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                <Pagination
                  count={Math.ceil(stats.total_vectors / 10)}
                  page={page}
                  onChange={handlePageChange}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default VectorStoreDashboard; 