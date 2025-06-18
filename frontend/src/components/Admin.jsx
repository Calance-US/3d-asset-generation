import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';
import { toast } from 'react-toastify';
import VectorStoreDashboard from './admin/VectorStoreDashboard';
import { Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TablePagination, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { BASE_URL } from '../lib/utils';

// Initialize markdown parser
const mdParser = new MarkdownIt();

// Global styles for markdown content
const markdownStyles = `
  .markdown-content {
    color: #d1d5db;
  }
  .markdown-content h1,
  .markdown-content h2,
  .markdown-content h3,
  .markdown-content h4,
  .markdown-content h5,
  .markdown-content h6 {
    color: #ffffff;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
  }
  .markdown-content p {
    margin-bottom: 1em;
  }
  .markdown-content ul,
  .markdown-content ol {
    margin-left: 1.5em;
    margin-bottom: 1em;
  }
  .markdown-content li {
    margin-bottom: 0.5em;
  }
  .markdown-content code {
    background-color: #374151;
    padding: 0.2em 0.4em;
    border-radius: 0.25em;
    font-family: monospace;
  }
  .markdown-content pre {
    background-color: #374151;
    padding: 1em;
    border-radius: 0.5em;
    overflow-x: auto;
    margin-bottom: 1em;
  }
  .markdown-content pre code {
    background-color: transparent;
    padding: 0;
  }
  .markdown-content blockquote {
    border-left: 4px solid #4b5563;
    padding-left: 1em;
    margin-left: 0;
    margin-bottom: 1em;
    color: #9ca3af;
  }
  .markdown-content a {
    color: #60a5fa;
    text-decoration: underline;
  }
  .markdown-content a:hover {
    color: #93c5fd;
  }
  .markdown-content table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
  }
  .markdown-content th,
  .markdown-content td {
    border: 1px solid #4b5563;
    padding: 0.5em;
    text-align: left;
  }
  .markdown-content th {
    background-color: #374151;
  }
`;

function Admin() {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState(null);
  const [goldStandards, setGoldStandards] = useState([]);
  const [goldStandardsLoading, setGoldStandardsLoading] = useState(true);
  const [goldStandardsError, setGoldStandardsError] = useState(null);
  const [multiUploadFiles, setMultiUploadFiles] = useState([]);
  const [multiUploadId, setMultiUploadId] = useState(null);
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
  const [newGoldStandard, setNewGoldStandard] = useState({
    html: '',
    config: {},
    metadata: {
      topic: '',
      subject: '',
      tags: []
    }
  });
  const [previewHtml, setPreviewHtml] = useState('');
  const [previewConfig, setPreviewConfig] = useState({});
  const [isPreviewVisible, setIsPreviewVisible] = useState(false);
  const iframeRef = useRef(null);
  const navigate = useNavigate();
  const [analyzing, setAnalyzing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    loadPrompts();
    fetchStats();
    fetchGoldStandards();
  }, []);

  const fetchStats = async () => {
    try {
      setStatsLoading(true);
      const response = await fetch(`${BASE_URL}/admin/vector-store-stats`);
      if (!response.ok) {
        throw new Error('Failed to fetch generation stats');
      }
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setStatsError(err.message);
    } finally {
      setStatsLoading(false);
    }
  };

  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds.toFixed(2)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(2)}s`;
  };

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

  const handleAddGoldStandard = async () => {
    try {
      const formData = new FormData();
      const htmlBlob = new Blob([newGoldStandard.html], { type: 'text/html' });
      formData.append('files', htmlBlob, 'visualization.html');

      const response = await fetch(`${BASE_URL}/gold-standards`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to add gold standard');
      }

      const data = await response.json();
      if (data.upload_id) {
        setMultiUploadId(data.upload_id);
        setMultiUploadPolling(true);
        toast.info('Upload started. Tracking status...');
      } else {
        toast.error('Failed to start upload.');
      }

      setNewGoldStandard({
        html: '',
        config: {},
        metadata: {
          topic: '',
          subject: '',
          tags: []
        }
      });
    } catch (err) {
      toast.error('Failed to add gold standard');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/gold-standards/search?query=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) {
        throw new Error('Failed to search gold standards');
      }
      const data = await response.json();
      setSearchResults(data);
      setError(null);
    } catch (err) {
      setError('Error searching gold standards: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        setNewGoldStandard(prev => ({
          ...prev,
          html: content
        }));
        setPreviewHtml(content);
        setIsPreviewVisible(true);
      };
      reader.readAsText(file);
    }
  };

  const handleConfigChange = (e) => {
    try {
      const config = JSON.parse(e.target.value);
      setNewGoldStandard(prev => ({
        ...prev,
        config
      }));
    } catch (err) {
      // Invalid JSON, ignore
    }
  };

  const handleFullscreen = () => {
    if (iframeRef.current) {
      if (iframeRef.current.requestFullscreen) {
        iframeRef.current.requestFullscreen();
      } else if (iframeRef.current.webkitRequestFullscreen) {
        iframeRef.current.webkitRequestFullscreen();
      } else if (iframeRef.current.msRequestFullscreen) {
        iframeRef.current.msRequestFullscreen();
      }
    }
  };

  // Multi-file upload handlers
  const handleMultiFileChange = (e) => {
    setMultiUploadFiles([...e.target.files]);
  };

  const handleMultiUpload = async () => {
    if (!multiUploadFiles.length) {
      toast.error('Please select at least one HTML file.');
      return;
    }
    const formData = new FormData();
    multiUploadFiles.forEach(file => formData.append('files', file));
    try {
      const response = await fetch(`${BASE_URL}/gold-standards/`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.upload_id) {
        setMultiUploadId(data.upload_id);
        setMultiUploadStatus('processing');
        setMultiUploadPolling(true);
        toast.info('Upload started. Tracking status...');
      } else {
        toast.error('Failed to start upload.');
      }
    } catch (err) {
      toast.error('Error uploading files.');
    }
  };

  useEffect(() => {
    if (!multiUploadId || !multiUploadPolling) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BASE_URL}/gold-standards/status/${multiUploadId}`);
        const statusData = await res.json();
        setMultiUploadStatus(statusData);
        if (statusData.status === 'completed' || statusData.status === 'error') {
          setMultiUploadPolling(false);
          clearInterval(interval);
          if (statusData.status === 'completed') {
            toast.success('Gold standards upload completed!');
          } else {
            toast.error('Gold standards upload failed.');
          }
        }
      } catch (err) {
        setMultiUploadPolling(false);
        clearInterval(interval);
        toast.error('Error polling upload status.');
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [multiUploadId, multiUploadPolling]);

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

  const truncateContent = (content) => {
    // Remove markdown syntax for preview
    const plainText = content.replace(/[#*`_~[]]/g, '');
    return plainText.length > 150 ? plainText.substring(0, 150) + '...' : plainText;
  };

  if (loading || statsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (error || statsError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-red-500">{error || statsError}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Home Button */}
      <div className="mb-4 flex justify-between items-center">
        <Button
          variant="outlined"
          color="primary"
          onClick={() => navigate('/')}
          sx={{ color: '#3B82F6', borderColor: '#3B82F6', '&:hover': { backgroundColor: 'rgba(59, 130, 246, 0.1)' } }}
        >
          Home
        </Button>
        {/* You can add other header content here if needed */}
      </div>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
        
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
                        setMultiUploadId(data.upload_id);
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
                              setMultiUploadId(null);
                              
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
                    className={`px-4 py-2 rounded transition-colors ${
                      multiUploadFiles.length === 0 || multiUploadPolling
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
                                <span className={`px-2 py-1 rounded-full text-xs ${
                                  standard.metadata.validation_status === 'validated' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                                }`}>
                                  {standard.metadata.validation_status}
                                </span>
                              </TableCell>
                              <TableCell className="text-gray-300">
                                <span className={`px-2 py-1 rounded-full text-xs ${
                                  standard.metadata.validation_status === 'validated' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
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
      </div>
    </div>
  );
}

export default Admin; 