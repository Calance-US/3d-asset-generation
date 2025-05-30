import React, { useState, useEffect, useRef } from 'react';

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("openai");
  const [subject, setSubject] = useState("physics");
  const [html, setHtml] = useState("");
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const iframeRef = useRef(null);  // Add ref for iframe

  // Load history on component mount
  useEffect(() => {
    loadHistory();
  }, []); // Empty dependency array to run only once on mount

  // Add fullscreen handler
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

  async function loadHistory() {
    try {
      const res = await fetch("http://localhost:8000/history");
      const data = await res.json();
      console.log("Loaded history:", data.entries); // Debug log
      setHistory(data.entries);
    } catch (err) {
      console.error("Error loading history:", err);
    }
  }

  async function handleGenerate() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          topic: prompt,
          provider: provider,
          subject: subject
        })
      });
      const data = await res.json();
      setHtml(data.html);
      loadHistory();
    } catch (err) {
      setError(`Error generating scene: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function loadHistoryEntry(entryId) {
    try {
      const res = await fetch(`http://localhost:8000/history/${entryId}`);
      const entry = await res.json();
      setPrompt(entry.prompt);
      setProvider(entry.provider);
      setSubject(entry.subject || "physics");
      setHtml(entry.html);
    } catch (err) {
      setError(`Error loading history entry: ${err.message}`);
    }
  }

  async function handleReset() {
    setPrompt("");
    setProvider("openai");
    setSubject("physics");
    setHtml("");
    setError("");
  }

  async function handleDeleteEntry(entryId, event) {
    event.stopPropagation(); // Prevent triggering the parent div's onClick
    try {
      const res = await fetch(`http://localhost:8000/history/${entryId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        // Reload history after successful deletion
        loadHistory();
      } else {
        setError('Failed to delete history entry');
      }
    } catch (err) {
      setError(`Error deleting history entry: ${err.message}`);
    }
  }

  async function handleDownload(entry, event) {
    event.stopPropagation(); // Prevent triggering the parent div's onClick
    try {
      // Create a blob from the HTML content
      const blob = new Blob([entry.html], { type: 'text/html' });
      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);
      // Create a temporary link element
      const link = document.createElement('a');
      link.href = url;
      // Set the filename using the prompt and timestamp
      const timestamp = new Date(entry.timestamp).toISOString().split('T')[0];
      const filename = `visualization_${timestamp}_${entry.prompt.slice(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase()}.html`;
      link.download = filename;
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      // Clean up the URL
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Error downloading file: ${err.message}`);
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">3D Concept Visualizer</h1>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
          >
            {showHistory ? "Hide History" : "Show History"}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* History Panel */}
          {showHistory && (
            <div className="lg:col-span-1">
              <div className="bg-gray-800 shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-white mb-4">Generation History</h2>
                <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
                  {history.length === 0 ? (
                    <p className="text-gray-400 text-center py-4">No history available</p>
                  ) : (
                    history.map((entry) => (
                      <div
                        key={entry.id}
                        onClick={() => loadHistoryEntry(entry.id)}
                        className="p-4 border border-gray-700 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors duration-150"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm text-gray-300">
                              {entry.prompt}
                            </p>
                            <p className="text-xs text-gray-400 mt-2">
                              {new Date(entry.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-900 text-purple-200">
                              {entry.provider}
                            </span>
                            <button
                              onClick={(e) => handleDownload(entry, e)}
                              className="p-1 text-gray-400 hover:text-green-400 focus:outline-none"
                              title="Download HTML"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                            </button>
                            <button
                              onClick={(e) => handleDeleteEntry(entry.id, e)}
                              className="p-1 text-gray-400 hover:text-red-400 focus:outline-none"
                              title="Delete entry"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={`${showHistory ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
            <div className="bg-gray-800 shadow rounded-lg p-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300">
                    Enter Concept Prompt
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                    rows={4}
                    placeholder="e.g., 'Explain Ohm's Law using a 3D electric circuit'"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300">
                    Choose AI Provider
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  >
                    <option value="openai">OpenAI (GPT-4)</option>
                    <option value="ollama">Ollama (local)</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300">
                    Choose Subject
                  </label>
                  <select
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  >
                    <option value="physics">Physics</option>
                    <option value="chemistry">Chemistry</option>
                    <option value="biology">Biology</option>
                    <option value="mathematics">Mathematics</option>
                  </select>
                </div>

                <div className="flex space-x-4">
                  <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className={`flex-1 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 ${
                      loading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {loading ? 'Generating...' : 'Generate Scene'}
                  </button>

                  <button
                    onClick={handleReset}
                    className="flex justify-center py-2 px-4 border border-gray-700 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                  >
                    Reset
                  </button>
                </div>

                {error && (
                  <div className="rounded-md bg-red-900/50 p-4">
                    <div className="flex">
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-200">Error</h3>
                        <div className="mt-2 text-sm text-red-300">{error}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {html && (
                <div className="mt-8">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-medium text-white">Generated Visualization</h2>
                    <button
                      onClick={handleFullscreen}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-700 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                      </svg>
                      Fullscreen
                    </button>
                  </div>
                  <div className="border border-gray-700 rounded-lg overflow-hidden">
                    <iframe
                      ref={iframeRef}
                      srcDoc={html}
                      className="w-full h-[60vh]"
                      title="3D Visualization"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
