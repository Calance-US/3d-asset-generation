import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';
import { toast } from 'react-toastify';

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
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [editForm, setEditForm] = useState({
    topic: "",
    content: "",
    subject: "",
    tags: ""
  });
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState(null);
  const [goldStandards, setGoldStandards] = useState([]);
  const [goldStandardsLoading, setGoldStandardsLoading] = useState(true);
  const [goldStandardsError, setGoldStandardsError] = useState(null);
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
      const response = await fetch('http://localhost:8000/admin/generation-stats');
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
      const response = await fetch("http://localhost:8000/admin/prompts");
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
      const response = await fetch('http://localhost:8000/api/v1/gold-standards/');
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

  const handleEdit = (promptId) => {
    const prompt = prompts.find(p => p.id === promptId);
    if (prompt) {
      setEditingPrompt(prompt);
      setEditForm({
        topic: prompt.topic,
        content: prompt.content,
        subject: prompt.subject,
        tags: prompt.tags.join(", ")
      });
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`http://localhost:8000/admin/prompts/${editingPrompt.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: editForm.topic,
          content: editForm.content,
          subject: editForm.subject,
          tags: editForm.tags.split(",").map(tag => tag.trim()).filter(tag => tag)
        }),
      });

      if (response.ok) {
        const updatedPrompt = await response.json();
        setPrompts(prompts.map(p => p.id === editingPrompt.id ? updatedPrompt : p));
        setEditingPrompt(null);
      } else {
        setError("Failed to update prompt");
      }
    } catch (err) {
      setError("Error connecting to server");
    }
  };

  const handleDelete = async (index) => {
    if (!window.confirm('Are you sure you want to delete this gold standard?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/gold-standards/${index}`, {
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

  const handleAddGoldStandard = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/gold-standards', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newGoldStandard)
      });

      if (!response.ok) {
        throw new Error('Failed to add gold standard');
      }

      toast.success('Gold standard added successfully');
      fetchGoldStandards();
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
      const response = await fetch(`http://localhost:8000/api/v1/gold-standards/search?query=${encodeURIComponent(searchQuery)}`);
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

  const analyzeHtml = async () => {
    if (!newGoldStandard.html) {
      toast.error('Please upload an HTML file first');
      return;
    }

    try {
      setAnalyzing(true);
      const response = await fetch('http://localhost:8000/api/v1/gold-standards/analyze', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          html: newGoldStandard.html
        })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze HTML');
      }

      const data = await response.json();
      
      // Update the gold standard with extracted information
      setNewGoldStandard(prev => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          topic: data.topic_name || prev.metadata.topic
        },
        config: {
          ...data,
          three_js_url: "https://esm.sh/three@0.155.0",
          orbit_controls_url: "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
          camera_controls: "OrbitControls",
          curve_points: [{ x: 0, y: 0, z: 0 }],
          animation_speed: 1.0,
          tts_language: "en-US",
          tts_rate: 1.0,
          tts_pitch: 1.0,
          renderer: {
            antialias: data.renderer?.antialias ?? true,
            shadowMapEnabled: data.renderer?.shadowMapEnabled ?? true,
            shadowMapType: data.renderer?.shadowMapType || "PCFSoftShadowMap",
            outputColorSpace: data.renderer?.outputColorSpace || "SRGBColorSpace",
            toneMapping: data.renderer?.toneMapping || "ACESFilmicToneMapping",
            toneMappingExposure: data.renderer?.toneMappingExposure ?? 1.0
          }
        }
      }));

      toast.success('HTML analyzed successfully');
    } catch (err) {
      console.error('Error analyzing HTML:', err);
      toast.error('Failed to analyze HTML');
    } finally {
      setAnalyzing(false);
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
    <div className="min-h-screen bg-gray-900 p-8">
      <style>{markdownStyles}</style>
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Back to Generator
          </button>
        </div>

        {/* Generation Statistics Section */}
        <div className="bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white">Visualization Generation Statistics</h2>
            <button
              onClick={fetchStats}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Refresh Statistics
            </button>
          </div>
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-300">Mean Generation Time</h3>
                <p className="text-2xl font-bold text-white">{formatTime(stats.mean)}</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-300">Median Generation Time</h3>
                <p className="text-2xl font-bold text-white">{formatTime(stats.median)}</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-300">95th Percentile</h3>
                <p className="text-2xl font-bold text-white">{formatTime(stats.p95)}</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-300">Total Generations</h3>
                <p className="text-2xl font-bold text-white">{stats.total_generations}</p>
              </div>
            </div>
          )}
        </div>

        {/* Prompts Section */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Prompts</h2>
          <div className="flex flex-col gap-4">
            {prompts.map((prompt) => (
              <div key={prompt.id} className="bg-gray-700 p-4 rounded-lg">
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-white mb-2">{prompt.topic}</h3>
                    <p className="text-gray-300 mb-4">{truncateContent(prompt.content)}</p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-purple-600 text-white text-sm rounded">
                        {prompt.subject}
                      </span>
                      {prompt.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-600 text-white text-sm rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4 flex-shrink-0">
                    <button
                      onClick={() => handleEdit(prompt.id)}
                      className="text-blue-400 hover:text-blue-300"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(prompt.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Gold Standards Section */}
        <div className="bg-gray-800 shadow rounded-lg p-6 mt-8">
          <h2 className="text-xl font-semibold text-white mb-4">Gold Standards</h2>
          
          {/* Add New Gold Standard */}
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">Add New Gold Standard</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300">HTML File</label>
                <div className="flex gap-2">
                  <input
                    type="file"
                    accept=".html"
                    onChange={handleFileUpload}
                    className="flex-1 mt-1 block w-full text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                  />
                  <button
                    onClick={analyzeHtml}
                    disabled={analyzing || !newGoldStandard.html}
                    className="mt-1 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {analyzing ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      "Analyze HTML"
                    )}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300">Topic</label>
                <input
                  type="text"
                  value={newGoldStandard.metadata.topic}
                  onChange={(e) => setNewGoldStandard({
                    ...newGoldStandard,
                    metadata: { ...newGoldStandard.metadata, topic: e.target.value }
                  })}
                  className="mt-1 block w-full rounded-md bg-gray-800 border-gray-600 text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300">Subject</label>
                <input
                  type="text"
                  value={newGoldStandard.metadata.subject}
                  onChange={(e) => setNewGoldStandard({
                    ...newGoldStandard,
                    metadata: { ...newGoldStandard.metadata, subject: e.target.value }
                  })}
                  className="mt-1 block w-full rounded-md bg-gray-800 border-gray-600 text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300">Configuration (JSON)</label>
                <textarea
                  value={JSON.stringify(newGoldStandard.config, null, 2)}
                  onChange={handleConfigChange}
                  rows={5}
                  className="mt-1 block w-full rounded-md bg-gray-800 border-gray-600 text-white font-mono"
                />
              </div>
              <button
                onClick={handleAddGoldStandard}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                Add Gold Standard
              </button>
            </div>
          </div>

          {/* Preview Section */}
          {isPreviewVisible && (
            <div className="bg-gray-700 rounded-lg p-4 mb-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-white">Preview</h3>
                <button
                  onClick={handleFullscreen}
                  className="flex items-center px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5"
                    />
                  </svg>
                  Fullscreen
                </button>
              </div>
              <div className="border border-gray-700 rounded-lg overflow-hidden">
                <iframe
                  ref={iframeRef}
                  srcDoc={previewHtml}
                  className="w-full h-[60vh]"
                  title="HTML Preview"
                  sandbox="allow-scripts"
                />
              </div>
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-300 mb-2">HTML Content</h4>
                <div className="bg-gray-800 rounded-lg p-4">
                  <pre className="text-sm text-gray-400 overflow-x-auto">
                    {previewHtml.substring(0, 200)}...
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Search Section */}
          <div className="mb-8">
            <div className="flex gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search gold standards..."
                className="flex-1 px-4 py-2 rounded bg-gray-700 text-white focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleSearch}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>

          {/* Error Display */}
          {goldStandardsError && (
            <div className="mb-4 p-4 bg-red-900/50 border border-red-500 rounded">
              {goldStandardsError}
            </div>
          )}

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Search Results</h2>
              <div className="space-y-4">
                {searchResults.map((result, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-medium text-white">{result.metadata?.topic}</h3>
                        <p className="text-gray-300">{result.metadata?.subject}</p>
                        <div className="mt-2">
                          <pre className="text-sm text-gray-400 overflow-x-auto">
                            {result.metadata?.html ? result.metadata.html.substring(0, 200) + '...' : 'No HTML content'}
                          </pre>
                        </div>
                        {result.distance && (
                          <p className="text-sm text-gray-400 mt-2">
                            Similarity Score: {(1 - result.distance).toFixed(2)}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => handleDelete(result.id)}
                        className="px-3 py-1 bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gold Standards List */}
          <div>
            <h2 className="text-xl font-semibold mb-4">All Gold Standards</h2>
            <div className="space-y-4">
              {goldStandards.map((standard, index) => (
                <div key={index} className="bg-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-medium text-white">{standard.metadata?.topic}</h3>
                      <p className="text-gray-300">{standard.metadata?.subject}</p>
                      <div className="mt-2">
                        <pre className="text-sm text-gray-400 overflow-x-auto">
                          {standard.metadata?.html ? standard.metadata.html.substring(0, 200) + '...' : 'No HTML content'}
                        </pre>
                      </div>
                      {standard.distance && (
                        <p className="text-sm text-gray-400 mt-2">
                          Similarity Score: {(1 - standard.distance).toFixed(2)}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(standard.id)}
                      className="px-3 py-1 bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {editingPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl">
            <h2 className="text-2xl font-bold text-white mb-4">Edit Prompt</h2>
            <form onSubmit={handleEditSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 mb-2">Topic</label>
                  <input
                    type="text"
                    value={editForm.topic}
                    onChange={(e) => setEditForm({ ...editForm, topic: e.target.value })}
                    className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 mb-2">Content (Markdown)</label>
                  <div className="border border-gray-600 rounded">
                    <MdEditor
                      value={editForm.content}
                      style={{ height: '400px' }}
                      renderHTML={(text) => mdParser.render(text)}
                      onChange={({ text }) => setEditForm({ ...editForm, content: text })}
                      config={{
                        view: {
                          menu: true,
                          md: true,
                          html: true,
                          fullScreen: true,
                          hideMenu: false,
                        },
                        canView: {
                          menu: true,
                          md: true,
                          html: true,
                          fullScreen: true,
                          hideMenu: false,
                        },
                      }}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-gray-300 mb-2">Subject</label>
                  <input
                    type="text"
                    value={editForm.subject}
                    onChange={(e) => setEditForm({ ...editForm, subject: e.target.value })}
                    className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 mb-2">Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={editForm.tags}
                    onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                    className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                    placeholder="tag1, tag2, tag3"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setEditingPrompt(null)}
                  className="px-4 py-2 border border-gray-600 text-gray-300 rounded hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Admin; 