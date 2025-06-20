import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from 'react-toastify';
import VectorStoreDashboard from './admin/VectorStoreDashboard';
import ValidationMetrics from './admin/ValidationMetrics';
import { Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TablePagination, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { BASE_URL } from '../lib/utils';
import { adminAPI, get } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import UserMenu from './auth/UserMenu';

function Admin() {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState(null);
  const [goldStandards, setGoldStandards] = useState([]);
  const [goldStandardsLoading, setGoldStandardsLoading] = useState(true);
  const [goldStandardsError, setGoldStandardsError] = useState(null);
  const [multiUploadFiles, setMultiUploadFiles] = useState([]);
  const [multiUploadStatus, setMultiUploadStatus] = useState(null);
  const [multiUploadPolling, setMultiUploadPolling] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [editingGoldStandard, setEditingGoldStandard] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    id: '',
    snippet_hash: '',
    topic: '',
    subject: '',
    key_concepts: '',
    education_level: '',
    learning_objectives: '',
    html: '',
    type: '',
    status: '',
    validation_status: '',
    snippet_type: '',
    html_snippet: '',
    summary: '',
    embedding_text: '',
    filename: '',
    upload_id: '',
    llm_version: '',
    validation_errors: [],
    retry_count: 0,
    tags: []
  });

  // Redirect non-admin users
  useEffect(() => {
    if (!isAdmin()) {
      navigate('/');
      toast.error('Admin access required');
    }
  }, [isAdmin, navigate]);

  // Task Manager state
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedTaskDetails, setSelectedTaskDetails] = useState(null);
  const [taskDetailsLoading, setTaskDetailsLoading] = useState(false);
  const [taskPollingInterval, setTaskPollingInterval] = useState(null);

  useEffect(() => {
    loadPrompts();
    fetchGoldStandards();
  }, []);

  // Cleanup polling interval when component unmounts or task changes
  useEffect(() => {
    return () => {
      if (taskPollingInterval) {
        clearInterval(taskPollingInterval);
      }
    };
  }, [taskPollingInterval]);

  // Fetch tasks list
  const fetchTasks = async () => {
    try {
      setTasksLoading(true);
      setTasksError(null);
      const response = await fetch(`${BASE_URL}/admin/tasks`);
      if (!response.ok) {
        throw new Error('Failed to fetch tasks');
      }
      const data = await response.json();
      setTasks(data || []);
    } catch (err) {
      setTasksError('Error fetching tasks: ' + err.message);
      toast.error('Failed to load tasks');
    } finally {
      setTasksLoading(false);
    }
  };

  // Fetch detailed task information
  const fetchTaskDetails = async (taskId) => {
    try {
      setTaskDetailsLoading(true);
      const response = await fetch(`${BASE_URL}/admin/tasks/${taskId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch task details');
      }
      const data = await response.json();
      setSelectedTaskDetails(data);
    } catch (err) {
      toast.error('Failed to load task details: ' + err.message);
    } finally {
      setTaskDetailsLoading(false);
    }
  };

  // Start polling for selected task
  const startTaskPolling = (taskId) => {
    // Clear existing polling interval
    if (taskPollingInterval) {
      clearInterval(taskPollingInterval);
    }

    // Fetch initial data
    fetchTaskDetails(taskId);

    // Set up polling interval (10 seconds)
    const interval = setInterval(() => {
      fetchTaskDetails(taskId);
    }, 10000);

    setTaskPollingInterval(interval);
  };

  // Stop task polling
  const stopTaskPolling = () => {
    if (taskPollingInterval) {
      clearInterval(taskPollingInterval);
      setTaskPollingInterval(null);
    }
  };

  // Handle task selection
  const handleTaskSelect = (task) => {
    setSelectedTask(task);
    setSelectedTaskDetails(null);
    startTaskPolling(task.id);
  };

  // Manual refresh task details
  const refreshTaskDetails = () => {
    if (selectedTask) {
      fetchTaskDetails(selectedTask.id);
    }
  };

  // Manual refresh tasks list
  const refreshTasksList = () => {
    fetchTasks();
  };

  // Load tasks when Task Manager tab is selected
  useEffect(() => {
    if (activeTab === 4) {
      fetchTasks();
    } else {
      // Stop polling when switching away from Task Manager tab
      stopTaskPolling();
      setSelectedTask(null);
      setSelectedTaskDetails(null);
    }
  }, [activeTab]);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BASE_URL}/prompt`);
      if (!response.ok) {
        throw new Error(`Failed to load prompts: ${response.statusText}`);
      }
      const data = await response.json();
      setPrompts(data.prompts || []);
    } catch (err) {
      setError(`Error loading prompts: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchGoldStandards = async () => {
    try {
      const response = await fetch(`${BASE_URL}/gold-standards/`);
      if (!response.ok) {
        throw new Error('Failed to fetch gold standards');
      }
      const data = await response.json();
      setGoldStandards(data);
      setGoldStandardsError(null);
    } catch (err) {
      setGoldStandardsError('Error fetching gold standards: ' + err.message);
      toast.error('Failed to load gold standards');
    } finally {
      setGoldStandardsLoading(false);
    }
  };

  const handleEditGoldStandard = (standard) => {
    setEditingGoldStandard(standard);
    setEditForm({
      id: standard.metadata.id || '',
      snippet_hash: standard.metadata.snippet_hash || '',
      topic: standard.metadata.topic || '',
      subject: standard.metadata.subject || '',
      key_concepts: standard.metadata.key_concepts || '',
      education_level: standard.metadata.education_level || '',
      learning_objectives: standard.metadata.learning_objectives || '',
      html: standard.html || '',
      type: standard.type || '',
      status: standard.status || '',
      validation_status: standard.metadata.validation_status || '',
      snippet_type: standard.metadata.snippet_type || '',
      html_snippet: standard.metadata.html_snippet || '',
      summary: standard.metadata.summary || '',
      embedding_text: standard.metadata.embedding_text || '',
      filename: standard.metadata.filename || '',
      upload_id: standard.metadata.upload_id || '',
      llm_version: standard.metadata.llm_version || '',
      validation_errors: standard.metadata.validation_errors || [],
      retry_count: standard.metadata.retry_count || 0,
      tags: standard.metadata.tags || []
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = async () => {
    try {
      const response = await fetch(`${BASE_URL}/gold-standards/${editingGoldStandard.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          html: editForm.html,
          metadata: {
            id: editForm.id,
            snippet_hash: editForm.snippet_hash,
            topic: editForm.topic,
            subject: editForm.subject,
            key_concepts: editForm.key_concepts,
            education_level: editForm.education_level,
            learning_objectives: editForm.learning_objectives,
            validation_status: editForm.validation_status,
            snippet_type: editForm.snippet_type,
            html_snippet: editForm.html_snippet,
            summary: editForm.summary,
            embedding_text: editForm.embedding_text,
            filename: editForm.filename,
            upload_id: editForm.upload_id,
            llm_version: editForm.llm_version,
            validation_errors: editForm.validation_errors,
            retry_count: editForm.retry_count,
            tags: editForm.tags
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update gold standard');
      }

      toast.success('Gold standard updated successfully');
      setEditDialogOpen(false);
      fetchGoldStandards();
    } catch (err) {
      toast.error('Failed to update gold standard: ' + err.message);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleDelete = async (index) => {
    if (!window.confirm('Are you sure you want to delete this gold standard?')) {
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/gold-standards/${index}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete gold standard');
      }

      // Refresh the list after deletion
      fetchGoldStandards();
      setError(null);
    } catch (err) {
      setError('Error deleting gold standard: ' + err.message);
    }
  };

  if (loading || goldStandardsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 border border-blue-600 text-sm font-medium rounded-md text-blue-400 hover:bg-blue-600 hover:text-white transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Generator
          </Link>
          <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
        </div>
        <div className="flex items-center space-x-4">
          {user && (
            <div className="text-sm text-gray-300">
              <span>Logged in as:</span>
              <span className="ml-2 font-medium text-white">{user.firstName || user.username}</span>
              <span className="ml-2 px-2 py-1 bg-red-600 text-xs rounded-full">Admin</span>
            </div>
          )}
          <UserMenu />
        </div>
      </div>
      <div className="max-w-7xl mx-auto">


        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          className="mb-6"
          sx={{
            '& .MuiTab-root': {
              color: 'rgba(255, 255, 255, 0.7)',
              '&.Mui-selected': {
                color: '#60a5fa',
              },
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#60a5fa',
            },
          }}
        >
          <Tab label="Gold Standards" />
          <Tab label="Prompts" />
          <Tab label="FAISS Dashboard" />
          <Tab label="Validation Metrics" />
          <Tab label="Task Manager" />
        </Tabs>

        {activeTab === 0 && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Gold Standards</h2>

              {/* Multi-file Upload Section */}
              <div className="mb-6 bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-3">Upload Multiple Gold Standards</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-gray-300 mb-2">HTML Files</label>
                    <input
                      type="file"
                      accept=".html"
                      multiple
                      onChange={(e) => {
                        const files = Array.from(e.target.files);
                        setMultiUploadFiles(files);
                      }}
                      className="block w-full text-sm text-gray-300
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-blue-500 file:text-white
                        hover:file:bg-blue-600"
                    />
                    {multiUploadFiles.length > 0 && (
                      <p className="mt-2 text-gray-300 text-sm">
                        Selected {multiUploadFiles.length} file(s)
                      </p>
                    )}
                  </div>

                  <button
                    onClick={async () => {
                      if (multiUploadFiles.length === 0) {
                        toast.error('Please select files to upload');
                        return;
                      }

                      try {
                        // Create FormData
                        const formData = new FormData();
                        multiUploadFiles.forEach(file => {
                          formData.append('files', file);
                        });

                        // Start upload
                        const response = await fetch(`${BASE_URL}/gold-standards/`, {
                          method: 'POST',
                          body: formData,
                        });

                        if (!response.ok) {
                          throw new Error('Failed to start bulk upload');
                        }

                        const data = await response.json();
                        setMultiUploadStatus('processing');
                        setMultiUploadPolling(true);

                        // Start polling for status
                        const pollInterval = setInterval(async () => {
                          try {
                            const statusResponse = await fetch(`${BASE_URL}/gold-standards/status/${data.upload_id}`);
                            if (!statusResponse.ok) {
                              throw new Error('Failed to get upload status');
                            }

                            const statusData = await statusResponse.json();
                            setMultiUploadStatus(statusData.status);

                            if (statusData.status === 'completed' || statusData.status === 'failed') {
                              clearInterval(pollInterval);
                              setMultiUploadPolling(false);
                              setMultiUploadFiles([]);

                              if (statusData.status === 'completed') {
                                toast.success('Files uploaded successfully');
                                fetchGoldStandards(); // Refresh the list
                              } else {
                                toast.error('Upload failed: ' + statusData.error);
                              }
                            }
                          } catch (err) {
                            clearInterval(pollInterval);
                            setMultiUploadPolling(false);
                            toast.error('Error checking upload status: ' + err.message);
                          }
                        }, 2000); // Poll every 2 seconds

                      } catch (err) {
                        toast.error('Error starting upload: ' + err.message);
                      }
                    }}
                    disabled={multiUploadFiles.length === 0 || multiUploadPolling}
                    className={`px-4 py-2 rounded transition-colors ${multiUploadFiles.length === 0 || multiUploadPolling
                      ? 'bg-gray-500 cursor-not-allowed'
                      : 'bg-blue-500 hover:bg-blue-600 text-white'
                      }`}
                  >
                    {multiUploadPolling ? 'Uploading...' : 'Upload Files'}
                  </button>

                  {multiUploadStatus && (
                    <div className="mt-2">
                      <p className="text-gray-300 text-sm">
                        Status: {typeof multiUploadStatus === 'object' ? multiUploadStatus.status : multiUploadStatus}
                      </p>
                      {typeof multiUploadStatus === 'object' && multiUploadStatus.error_message && (
                        <p className="text-red-400 text-sm mt-1">
                          Error: {multiUploadStatus.error_message}
                        </p>
                      )}
                      {typeof multiUploadStatus === 'object' && multiUploadStatus.result && (
                        <div className="mt-2">
                          <p className="text-gray-300 text-sm font-medium">Results:</p>
                          <div className="bg-gray-800 p-2 rounded mt-1">
                            {multiUploadStatus.result.map((result, index) => (
                              <div key={index} className="mb-2">
                                <p className="text-gray-300 text-sm">
                                  File: {result.filename} - {result.status}
                                </p>
                                {result.error && (
                                  <p className="text-red-400 text-sm mt-1">
                                    Error: {result.error}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {goldStandardsLoading ? (
                <div className="text-center py-4">Loading...</div>
              ) : goldStandardsError ? (
                <div className="text-red-500">{goldStandardsError}</div>
              ) : (
                <div className="overflow-hidden rounded-lg border border-gray-700">
                  <TableContainer component={Paper} className="bg-gray-800">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell className="text-gray-300">ID</TableCell>
                          <TableCell className="text-gray-300">Topic</TableCell>
                          <TableCell className="text-gray-300">Snippet Type</TableCell>
                          <TableCell className="text-gray-300">Summary</TableCell>
                          <TableCell className="text-gray-300">Status</TableCell>
                          <TableCell className="text-gray-300">Validation</TableCell>
                          <TableCell className="text-gray-300">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {goldStandards
                          .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                          .map((standard) => (
                            <TableRow key={standard.metadata.id} className="hover:bg-gray-700">
                              <TableCell className="text-gray-300">{standard.metadata.id}</TableCell>
                              <TableCell className="text-gray-300">{standard.metadata.topic}</TableCell>
                              <TableCell className="text-gray-300">{standard.metadata.snippet_type}</TableCell>
                              <TableCell className="text-gray-300">{standard.metadata.summary}</TableCell>
                              <TableCell className="text-gray-300">
                                <span className={`px-2 py-1 rounded-full text-xs ${standard.metadata.validation_status === 'validated' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                                  }`}>
                                  {standard.metadata.validation_status}
                                </span>
                              </TableCell>
                              <TableCell className="text-gray-300">
                                <span className={`px-2 py-1 rounded-full text-xs ${standard.metadata.validation_status === 'validated' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                                  }`}>
                                  {standard.metadata.validation_status}
                                </span>
                              </TableCell>
                              <TableCell>
                                <div className="flex space-x-2">
                                  <IconButton
                                    size="small"
                                    onClick={() => handleEditGoldStandard(standard)}
                                    className="text-blue-400 hover:text-blue-300"
                                  >
                                    <EditIcon />
                                  </IconButton>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleDelete(standard.metadata.id)}
                                    className="text-red-400 hover:text-red-300"
                                  >
                                    <DeleteIcon />
                                  </IconButton>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                    <TablePagination
                      component="div"
                      count={goldStandards.length}
                      page={page}
                      onPageChange={handleChangePage}
                      rowsPerPage={rowsPerPage}
                      onRowsPerPageChange={handleChangeRowsPerPage}
                      className="text-gray-300"
                      rowsPerPageOptions={[5, 10, 25]}
                    />
                  </TableContainer>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Edit Dialog */}
        <Dialog
          open={editDialogOpen}
          onClose={() => setEditDialogOpen(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            style: {
              backgroundColor: '#1f2937',
              color: 'white',
              minHeight: '80vh'
            }
          }}
        >
          <DialogTitle sx={{
            borderBottom: '1px solid #374151',
            padding: '16px 24px',
            '& .MuiTypography-root': { color: 'white' }
          }}>
            Edit Gold Standard
          </DialogTitle>
          <DialogContent sx={{ padding: '24px' }}>
            <div className="space-y-6">
              {/* Basic Info Section */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <TextField
                    label="ID"
                    value={editForm.id}
                    disabled
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Topic"
                    value={editForm.topic}
                    onChange={(e) => setEditForm({ ...editForm, topic: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Subject"
                    value={editForm.subject}
                    onChange={(e) => setEditForm({ ...editForm, subject: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Type"
                    value={editForm.type}
                    onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                </div>
              </div>

              {/* Content Section */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Content</h3>
                <div className="space-y-4">
                  {/* <TextField
                    label="HTML Content"
                    value={editForm.html}
                    onChange={(e) => setEditForm({ ...editForm, html: e.target.value })}
                    multiline
                    rows={6}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  /> */}
                  <div>
                    <label className="block text-gray-300 mb-2">HTML Snippet</label>
                    <textarea
                      value={editForm.html_snippet}
                      onChange={(e) => setEditForm({ ...editForm, html_snippet: e.target.value })}
                      rows={8}
                      className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-y"
                      placeholder="Enter HTML snippet..."
                    />
                  </div>
                  <TextField
                    label="Summary"
                    value={editForm.summary}
                    onChange={(e) => setEditForm({ ...editForm, summary: e.target.value })}
                    multiline
                    rows={3}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                </div>
              </div>

              {/* Metadata Section */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Metadata</h3>
                <div className="grid grid-cols-2 gap-4">
                  <TextField
                    label="Key Concepts"
                    value={editForm.key_concepts}
                    onChange={(e) => setEditForm({ ...editForm, key_concepts: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Education Level"
                    value={editForm.education_level}
                    onChange={(e) => setEditForm({ ...editForm, education_level: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Learning Objectives"
                    value={editForm.learning_objectives}
                    onChange={(e) => setEditForm({ ...editForm, learning_objectives: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Tags"
                    value={editForm.tags}
                    onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                </div>
              </div>

              {/* Status Section */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Status Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <TextField
                    label="Status"
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Validation Status"
                    value={editForm.validation_status}
                    onChange={(e) => setEditForm({ ...editForm, validation_status: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Snippet Type"
                    value={editForm.snippet_type}
                    onChange={(e) => setEditForm({ ...editForm, snippet_type: e.target.value })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                  <TextField
                    label="Retry Count"
                    type="number"
                    value={editForm.retry_count}
                    onChange={(e) => setEditForm({ ...editForm, retry_count: parseInt(e.target.value) })}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: '#4B5563' },
                        '&:hover fieldset': { borderColor: '#6B7280' },
                        '&.Mui-focused fieldset': { borderColor: '#3B82F6' }
                      },
                      '& .MuiInputLabel-root': { color: '#9CA3AF' },
                      '& .MuiInputBase-input': { color: 'white' }
                    }}
                  />
                </div>
              </div>
            </div>
          </DialogContent>
          <DialogActions sx={{
            borderTop: '1px solid #374151',
            padding: '16px 24px'
          }}>
            <Button
              onClick={() => setEditDialogOpen(false)}
              sx={{
                color: '#9CA3AF',
                '&:hover': { backgroundColor: 'rgba(156, 163, 175, 0.1)' }
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleEditSubmit}
              variant="contained"
              sx={{
                backgroundColor: '#3B82F6',
                '&:hover': { backgroundColor: '#2563EB' }
              }}
            >
              Save Changes
            </Button>
          </DialogActions>
        </Dialog>

        {activeTab === 1 && (
          <div className="bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Prompts</h2>
            {loading ? (
              <div className="text-gray-400">Loading prompts...</div>
            ) : error ? (
              <div className="text-red-400">{error}</div>
            ) : (
              <div className="space-y-4">
                {prompts.map((prompt) => (
                  <div key={prompt.id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-medium text-white">{prompt.topic}</h3>
                        <p className="text-gray-300 text-sm">Subject: {prompt.subject}</p>
                        {prompt.category && (
                          <p className="text-gray-300 text-sm">Category: {prompt.category}</p>
                        )}
                        {prompt.tags && prompt.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-2">
                            {prompt.tags.map((tag, index) => (
                              <span
                                key={index}
                                className="bg-gray-600 text-gray-200 px-2 py-1 rounded text-xs"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="mt-2">
                      <p className="text-gray-300 whitespace-pre-wrap">{prompt.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 2 && (
          <div className="bg-gray-800 shadow rounded-lg p-6">
            <VectorStoreDashboard />
          </div>
        )}

        {activeTab === 3 && (
          <div className="bg-gray-800 shadow rounded-lg p-6">
            <ValidationMetrics />
          </div>
        )}

        {activeTab === 4 && (
          <div className="bg-gray-800 shadow rounded-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-white">Task Manager</h2>
              <Button
                variant="outlined"
                onClick={refreshTasksList}
                disabled={tasksLoading}
                className="text-blue-400 border-blue-400 hover:bg-blue-400 hover:text-white"
              >
                {tasksLoading ? 'Loading...' : 'Refresh Tasks'}
              </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Tasks List */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Active Tasks</h3>

                {tasksError && (
                  <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-4">
                    {tasksError}
                  </div>
                )}

                {tasksLoading ? (
                  <div className="text-gray-400 text-center py-8">Loading tasks...</div>
                ) : tasks.length === 0 ? (
                  <div className="text-gray-400 text-center py-8">No tasks found</div>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {tasks.map((task) => (
                      <div
                        key={task.id}
                        onClick={() => handleTaskSelect(task)}
                        className={`p-3 rounded cursor-pointer transition-colors ${selectedTask?.id === task.id
                          ? 'bg-blue-600 border border-blue-400'
                          : 'bg-gray-600 hover:bg-gray-500 border border-gray-500'
                          }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">
                              {task.id}
                            </p>
                            <p className="text-xs text-gray-300 mt-1">
                              Type: {task.task_type}
                            </p>
                            <div className="flex items-center mt-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${task.status === 'completed' ? 'bg-green-900 text-green-200' :
                                task.status === 'failed' ? 'bg-red-900 text-red-200' :
                                  task.status === 'running' ? 'bg-blue-900 text-blue-200' :
                                    'bg-yellow-900 text-yellow-200'
                                }`}>
                                {task.status}
                              </span>
                              <span className="text-xs text-gray-400 ml-2">
                                {task.progress_percentage}%
                              </span>
                            </div>
                          </div>
                        </div>
                        {task.current_stage && (
                          <p className="text-xs text-gray-400 mt-1">
                            Stage: {task.current_stage}
                          </p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          Created: {new Date(task.created_at).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Task Details */}
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-white">Task Details</h3>
                  {selectedTask && (
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={refreshTaskDetails}
                      disabled={taskDetailsLoading}
                      className="text-blue-400 border-blue-400 hover:bg-blue-400 hover:text-white"
                    >
                      {taskDetailsLoading ? 'Loading...' : 'Refresh'}
                    </Button>
                  )}
                </div>

                {!selectedTask ? (
                  <div className="text-gray-400 text-center py-8">
                    Select a task to view details
                  </div>
                ) : taskDetailsLoading ? (
                  <div className="text-gray-400 text-center py-8">Loading task details...</div>
                ) : selectedTaskDetails ? (
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {/* Task Overview */}
                    <div className="bg-gray-800 rounded p-3">
                      <h4 className="text-sm font-medium text-white mb-2">Overview</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-400">ID:</span>
                          <p className="text-white font-mono text-xs break-all">{selectedTaskDetails.id}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Type:</span>
                          <p className="text-white">{selectedTaskDetails.task_type}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Status:</span>
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${selectedTaskDetails.status === 'completed' ? 'bg-green-900 text-green-200' :
                            selectedTaskDetails.status === 'failed' ? 'bg-red-900 text-red-200' :
                              selectedTaskDetails.status === 'running' ? 'bg-blue-900 text-blue-200' :
                                'bg-yellow-900 text-yellow-200'
                            }`}>
                            {selectedTaskDetails.status}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-400">Progress:</span>
                          <p className="text-white">{selectedTaskDetails.progress_percentage}%</p>
                        </div>
                      </div>
                    </div>

                    {/* Timestamps */}
                    <div className="bg-gray-800 rounded p-3">
                      <h4 className="text-sm font-medium text-white mb-2">Timeline</h4>
                      <div className="space-y-1 text-xs">
                        <div>
                          <span className="text-gray-400">Created:</span>
                          <span className="text-white ml-2">
                            {selectedTaskDetails.created_at ? new Date(selectedTaskDetails.created_at).toLocaleString() : 'N/A'}
                          </span>
                        </div>
                        {selectedTaskDetails.started_at && (
                          <div>
                            <span className="text-gray-400">Started:</span>
                            <span className="text-white ml-2">
                              {new Date(selectedTaskDetails.started_at).toLocaleString()}
                            </span>
                          </div>
                        )}
                        {selectedTaskDetails.completed_at && (
                          <div>
                            <span className="text-gray-400">Completed:</span>
                            <span className="text-white ml-2">
                              {new Date(selectedTaskDetails.completed_at).toLocaleString()}
                            </span>
                          </div>
                        )}
                        {selectedTaskDetails.expires_at && (
                          <div>
                            <span className="text-gray-400">Expires:</span>
                            <span className="text-white ml-2">
                              {new Date(selectedTaskDetails.expires_at).toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Current Stage */}
                    {selectedTaskDetails.current_stage && (
                      <div className="bg-gray-800 rounded p-3">
                        <h4 className="text-sm font-medium text-white mb-2">Current Stage</h4>
                        <p className="text-blue-400 text-sm">{selectedTaskDetails.current_stage}</p>
                      </div>
                    )}

                    {/* Error Message */}
                    {selectedTaskDetails.error_message && (
                      <div className="bg-red-900 border border-red-700 rounded p-3">
                        <h4 className="text-sm font-medium text-red-200 mb-2">Error</h4>
                        <p className="text-red-100 text-xs">{selectedTaskDetails.error_message}</p>
                      </div>
                    )}

                    {/* Stages */}
                    {selectedTaskDetails.stages && selectedTaskDetails.stages.length > 0 && (
                      <div className="bg-gray-800 rounded p-3">
                        <h4 className="text-sm font-medium text-white mb-3">Stages</h4>
                        <div className="space-y-2">
                          {selectedTaskDetails.stages.map((stage, index) => (
                            <div key={index} className="border-l-2 border-gray-600 pl-3">
                              <div className="flex justify-between items-center">
                                <span className="text-sm text-white font-medium">{stage.name}</span>
                                <div className="flex items-center space-x-2">
                                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${stage.status === 'completed' ? 'bg-green-900 text-green-200' :
                                    stage.status === 'failed' ? 'bg-red-900 text-red-200' :
                                      stage.status === 'running' ? 'bg-blue-900 text-blue-200' :
                                        'bg-yellow-900 text-yellow-200'
                                    }`}>
                                    {stage.status}
                                  </span>
                                  <span className="text-xs text-gray-400">
                                    {stage.progress_percentage}%
                                  </span>
                                </div>
                              </div>
                              {stage.message && (
                                <p className="text-xs text-gray-400 mt-1">{stage.message}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Auto-refresh indicator */}
                    {taskPollingInterval && (
                      <div className="bg-blue-900 border border-blue-700 rounded p-2">
                        <p className="text-blue-200 text-xs flex items-center">
                          <span className="animate-pulse mr-2">●</span>
                          Auto-refreshing every 10 seconds
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-red-400 text-center py-8">
                    Failed to load task details
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Admin;
