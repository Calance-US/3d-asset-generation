import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Disclosure } from '@headlessui/react';
import { ChevronUpIcon } from '@heroicons/react/20/solid';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function Generator() {
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("openai");
  const [subject, setSubject] = useState("physics");
  const [html, setHtml] = useState("");
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const iframeRef = useRef(null);
  const [config, setConfig] = useState({
    topic_name: "",
    key_concepts: "",
    three_js_url: "https://esm.sh/three@0.155.0",
    orbit_controls_url: "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
    additional_imports_comment: "",
    education_level: "High School",
    learning_objectives: "",
    interactive_features: "",
    components: [],
    materials: [],
    lights: [],
    renderer: {
      antialias: true,
      shadowMapEnabled: true,
      shadowMapType: "PCFSoftShadowMap",
      outputColorSpace: "SRGBColorSpace",
      toneMapping: "ACESFilmicToneMapping",
      toneMappingExposure: 1.0
    },
    camera_controls: "OrbitControls",
    interactive_description: "",
    animated_elements: "",
    curve_points: [{ x: 0, y: 0, z: 0 }],
    animation_speed: 1.0,
    tts_language: "en-US",
    tts_rate: 1.0,
    tts_pitch: 1.0,
    intro_narration_texts: [],
    supporting_narration_texts: [],
    scene_description: ""
  });

  const [enhancing, setEnhancing] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  // Load history on component mount
  useEffect(() => {
    loadHistory();
  }, []);

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

  const loadHistory = async () => {
    try {
      const response = await fetch("http://localhost:8000/history");
      if (!response.ok) {
        throw new Error(`Failed to load history: ${response.statusText}`);
      }
      const data = await response.json();
      setHistory(data.entries || []);
    } catch (err) {
      setError(`Error loading history: ${err.message}`);
    }
  };

  async function handleGenerate() {
    if (!prompt) {
      console.warn("Attempting to generate with empty prompt");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      console.info("Starting generation process...");
      console.debug("Request details:", {
        prompt,
        provider,
        subject,
        config: {
          ...config,
          three_js_url: "https://esm.sh/three@0.155.0",
          orbit_controls_url: "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
          camera_controls: "OrbitControls",
          curve_points: [{ x: 0, y: 0, z: 0 }],
          animation_speed: 1.0,
          tts_language: "en-US",
          tts_rate: 1.0,
          tts_pitch: 1.0,
          renderer: {
            antialias: config?.renderer?.antialias ?? true,
            shadowMapEnabled: config?.renderer?.shadowMapEnabled ?? true,
            shadowMapType: config?.renderer?.shadowMapType || "PCFSoftShadowMap",
            outputColorSpace: config?.renderer?.outputColorSpace || "SRGBColorSpace",
            toneMapping: config?.renderer?.toneMapping || "ACESFilmicToneMapping",
            toneMappingExposure: config?.renderer?.toneMappingExposure ?? 1.0
          }
        }
      });

      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: prompt,
          provider: provider,
          subject: subject,
          config: {
            ...config,
            three_js_url: "https://esm.sh/three@0.155.0",
            orbit_controls_url: "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
            camera_controls: "OrbitControls",
            curve_points: [{ x: 0, y: 0, z: 0 }],
            animation_speed: 1.0,
            tts_language: "en-US",
            tts_rate: 1.0,
            tts_pitch: 1.0,
            renderer: {
              antialias: config?.renderer?.antialias ?? true,
              shadowMapEnabled: config?.renderer?.shadowMapEnabled ?? true,
              shadowMapType: config?.renderer?.shadowMapType || "PCFSoftShadowMap",
              outputColorSpace: config?.renderer?.outputColorSpace || "SRGBColorSpace",
              toneMapping: config?.renderer?.toneMapping || "ACESFilmicToneMapping",
              toneMappingExposure: config?.renderer?.toneMappingExposure ?? 1.0
            }
          }
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Generation failed:", errorData);
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.debug("Response data:", data);
      
      setHtml(data.html);
      console.info("Generation completed successfully");
    } catch (err) {
      console.error("Error during generation:", err);
      setError(`Error generating visualization: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  const handleEnhance = async () => {
    if (!prompt) {
      console.warn("Enhance attempted with empty prompt");
      setError("Please enter a prompt first");
      return;
    }

    console.info(`Starting prompt enhancement for: "${prompt}" using ${provider} provider`);
    setEnhancing(true);
    setError("");

    try {
      console.debug("Sending enhancement request to backend");
      const response = await fetch("http://localhost:8000/enhance-prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: prompt,
          provider,
          subject,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Enhancement request failed:", errorData);
        throw new Error(errorData.detail || "Failed to enhance prompt");
      }

      const enhancedData = await response.json();
      console.info("Successfully received enhanced configuration");
      console.debug("Enhanced configuration:", enhancedData);
      
      setConfig(prev => {
        const newConfig = {
          ...prev,
          topic_name: enhancedData.topic_name,
          key_concepts: enhancedData.key_concepts,
          education_level: enhancedData.education_level,
          learning_objectives: enhancedData.learning_objectives,
          interactive_features: enhancedData.interactive_features,
          components: enhancedData.components,
          materials: enhancedData.materials,
          lights: enhancedData.lights,
          interactive_description: enhancedData.interactive_description,
          animated_elements: enhancedData.animated_elements,
          scene_description: enhancedData.scene_description || '',
          intro_narration_texts: enhancedData.intro_narration_texts || [],
          supporting_narration_texts: enhancedData.supporting_narration_texts || [],
          renderer: {
            ...prev.renderer,
            antialias: enhancedData.renderer?.antialias ?? true,
            shadowMapEnabled: enhancedData.renderer?.shadowMapEnabled ?? true,
            shadowMapType: enhancedData.renderer?.shadowMapType || "PCFSoftShadowMap",
            outputColorSpace: enhancedData.renderer?.outputColorSpace || "SRGBColorSpace",
            toneMapping: enhancedData.renderer?.toneMapping || "ACESFilmicToneMapping",
            toneMappingExposure: enhancedData.renderer?.toneMappingExposure ?? 1.0
          }
        };
        console.debug("Updated configuration:", newConfig);
        return newConfig;
      });

    } catch (err) {
      console.error("Error during prompt enhancement:", err);
      setError(err.message);
    } finally {
      console.info("Prompt enhancement completed");
      setEnhancing(false);
    }
  };

  const handleHistorySelect = async (entry) => {
    try {
      // Set the prompt text
      setPrompt(entry.user_query || entry.prompt || '');
      
      // Set the provider and subject if available
      if (entry.provider && entry.provider !== 'Unknown') {
        setProvider(entry.provider);
      }
      if (entry.subject && entry.subject !== 'Unknown') {
        setSubject(entry.subject);
      }

      // Set the HTML content
      if (entry.response || entry.html) {
        setHtml(entry.response || entry.html);
      } else {
        // If HTML is not in the entry, fetch it from the server
        const response = await fetch(`http://localhost:8000/history/${entry.id}/html`);
        if (!response.ok) {
          throw new Error(`Failed to load HTML: ${response.statusText}`);
        }
        const data = await response.json();
        setHtml(data.html);
      }

      // Set the config if available
      if (entry.config) {
        // Parse JSON strings if they exist
        const components = entry.config.components || [];
        const materials = entry.config.materials || [];
        const lights = entry.config.lights || [];
        const renderSettings = entry.config.render_settings || {};
        const introNarrationTexts = entry.config.intro_narration_texts || [];
        const supportingNarrationTexts = entry.config.supporting_narration_texts || [];

        setConfig(prev => ({
          ...prev,
          // Basic fields
          topic_name: entry.config.topic_name || '',
          key_concepts: entry.config.key_concepts || '',
          education_level: entry.config.education_level || 'High School',
          learning_objectives: entry.config.learning_objectives || '',
          interactive_features: entry.config.interactive_features || '',
          interactive_description: entry.config.interactive_description || '',
          animated_elements: entry.config.animated_elements || '',
          scene_description: entry.config.scene_description || '',
          
          // Complex objects
          components: components,
          materials: materials,
          lights: lights,
          intro_narration_texts: introNarrationTexts,
          supporting_narration_texts: supportingNarrationTexts,
          
          // Required fields with defaults
          three_js_url: entry.config.three_js_url || "https://esm.sh/three@0.155.0",
          orbit_controls_url: entry.config.orbit_controls_url || "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
          camera_controls: entry.config.camera_controls || "OrbitControls",
          curve_points: entry.config.curve_points || [{ x: 0, y: 0, z: 0 }],
          animation_speed: entry.config.animation_speed || 1.0,
          tts_language: entry.config.tts_language || "en-US",
          tts_rate: entry.config.tts_rate || 1.0,
          tts_pitch: entry.config.tts_pitch || 1.0,
          
          // Renderer settings
          renderer: {
            antialias: renderSettings.antialias ?? true,
            shadowMapEnabled: renderSettings.shadowMapEnabled ?? true,
            shadowMapType: renderSettings.shadowMapType || "PCFSoftShadowMap",
            outputColorSpace: renderSettings.outputColorSpace || "SRGBColorSpace",
            toneMapping: renderSettings.toneMapping || "ACESFilmicToneMapping",
            toneMappingExposure: renderSettings.toneMappingExposure ?? 1.0
          }
        }));
      }

      setLoading(false);
      setError(null);
    } catch (err) {
      setError(`Error loading history entry: ${err.message}`);
      setLoading(false);
    }
  };

  async function handleReset() {
    setPrompt("");
    setProvider("openai");
    setSubject("physics");
    setHtml("");
    setError("");
    setConfig({
      topic_name: "",
      key_concepts: "",
      three_js_url: "https://esm.sh/three@0.155.0",
      orbit_controls_url: "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
      additional_imports_comment: "",
      education_level: "High School",
      learning_objectives: "",
      interactive_features: "",
      components: [],
      materials: [],
      lights: [],
      renderer: {
        antialias: true,
        shadowMapEnabled: true,
        shadowMapType: "PCFSoftShadowMap",
        outputColorSpace: "SRGBColorSpace",
        toneMapping: "ACESFilmicToneMapping",
        toneMappingExposure: 1.0
      },
      camera_controls: "OrbitControls",
      interactive_description: "",
      animated_elements: "",
      curve_points: [{ x: 0, y: 0, z: 0 }],
      animation_speed: 1.0,
      tts_language: "en-US",
      tts_rate: 1.0,
      tts_pitch: 1.0,
      intro_narration_texts: [],
      supporting_narration_texts: [],
      scene_description: ""
    });
  }

  async function handleDeleteEntry(entryId, event) {
    event.stopPropagation();
    try {
      const res = await fetch(`http://localhost:8000/history/${entryId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        loadHistory();
      } else {
        setError('Failed to delete history entry');
      }
    } catch (err) {
      setError(`Error deleting history entry: ${err.message}`);
    }
  }

  async function handleDownload(entry, event) {
    event.stopPropagation();
    try {
      const blob = new Blob([entry.response || entry.html], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date(entry.created_at || entry.timestamp).toISOString().split('T')[0];
      const filename = `visualization_${timestamp}_${(entry.user_query || entry.prompt).slice(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase()}.html`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Error downloading file: ${err.message}`);
    }
  }

  async function handleRegenerate() {
    if (!html) {
      console.warn("Attempting to regenerate with no existing visualization");
      return;
    }

    try {
      setRegenerating(true);
      setError(null);
      console.info("Starting regeneration process...");
      console.debug("Regeneration config:", config);

      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: prompt,
          provider: provider,
          subject: subject,
          config: config
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Regeneration failed:", errorData);
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.debug("Regeneration response data:", data);
      
      setHtml(data.html);
      console.info("Regeneration completed successfully");
    } catch (err) {
      console.error("Error during regeneration:", err);
      setError(`Error regenerating visualization: ${err.message}`);
    } finally {
      setRegenerating(false);
    }
  }

  // Add narration text management functions
  const addNarrationText = (type, text) => {
    setConfig(prev => ({
      ...prev,
      [type]: [...prev[type], text]
    }));
  };

  const removeNarrationText = (type, index) => {
    setConfig(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index)
    }));
  };

  const updateNarrationText = (type, index, text) => {
    setConfig(prev => ({
      ...prev,
      [type]: prev[type].map((t, i) => i === index ? text : t)
    }));
  };

  const handleSaveToLibrary = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/visualizations/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: prompt,
          subject: subject,
          html_content: html,
          config: config
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save visualization');
      }

      toast.success('Visualization saved to library successfully!', {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
      });
    } catch (error) {
      console.error('Error saving visualization:', error);
      toast.error('Failed to save visualization to library', {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
      });
    }
  };

  // Handler to fetch all retrieved results (for development)
  async function handleRetrieveSimilar() {
    if (!prompt) {
      console.warn("Attempting to retrieve with empty prompt");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("http://localhost:8000/retrieve-similar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: prompt,
          provider: provider,
          subject: subject,
          config: {
            ...config,
            three_js_url: "https://esm.sh/three@0.155.0",
            orbit_controls_url: "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
            camera_controls: "OrbitControls",
            curve_points: [{ x: 0, y: 0, z: 0 }],
            animation_speed: 1.0,
            tts_language: "en-US",
            tts_rate: 1.0,
            tts_pitch: 1.0,
            renderer: {
              antialias: config?.renderer?.antialias ?? true,
              shadowMapEnabled: config?.renderer?.shadowMapEnabled ?? true,
              shadowMapType: config?.renderer?.shadowMapType || "PCFSoftShadowMap",
              outputColorSpace: config?.renderer?.outputColorSpace || "SRGBColorSpace",
              toneMapping: config?.renderer?.toneMapping || "ACESFilmicToneMapping",
              toneMappingExposure: config?.renderer?.toneMappingExposure ?? 1.0
            }
          }
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Log the retrieval results to the console
      if (data.results) {
        console.log("Retrieved Results:", data.results);
        alert("Check the console for retrieved results.");
      } else {
        console.log("No retrieval results found in response.", data);
        alert("No retrieval results found in response.");
      }
    } catch (err) {
      setError(`Error retrieving similar visualizations: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <ToastContainer />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">3D Concept Visualizer</h1>
          <div className="flex space-x-4">
            <Link
              to="/admin"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Admin Dashboard
            </Link>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              {showHistory ? "Hide History" : "Show History"}
            </button>
          </div>
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
                        onClick={() => handleHistorySelect(entry)}
                        className="p-4 border border-gray-700 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors duration-150"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm text-gray-300">
                              {(entry.user_query || entry.prompt) && (entry.user_query || entry.prompt).length > 100 
                                ? `${(entry.user_query || entry.prompt).substring(0, 97)}...` 
                                : entry.user_query || entry.prompt || 'No prompt'}
                            </p>
                            <p className="text-xs text-gray-400 mt-2">
                              {new Date(entry.created_at || entry.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-900 text-purple-200">
                              {entry.subject || 'Unknown'}
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
                  <div className="mt-1 flex space-x-2">
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      className="flex-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                      rows={4}
                      placeholder="e.g., 'Explain Ohm's Law using a 3D electric circuit'"
                    />
                    <button
                      onClick={handleEnhance}
                      disabled={enhancing || !prompt}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {enhancing ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Enhancing...
                        </>
                      ) : (
                        "Enhance"
                      )}
                    </button>
                  </div>
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
                    <option value="gemini">Google (Gemini)</option>
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

                {/* Advanced Configuration Accordion */}
                <Disclosure>
                  {({ open }) => (
                    <>
                      <Disclosure.Button className="flex w-full justify-between rounded-lg bg-gray-900 px-4 py-2 text-left text-sm font-medium text-gray-300 hover:bg-gray-800 focus:outline-none focus-visible:ring focus-visible:ring-purple-500">
                        <span>Advanced Configuration</span>
                        <ChevronUpIcon
                          className={`${open ? 'rotate-180 transform' : ''} h-5 w-5 text-gray-300`}
                        />
                      </Disclosure.Button>
                      <Disclosure.Panel className="px-4 pt-4 pb-2 text-sm text-gray-300 space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300">
                            Key Concepts
                          </label>
                          <textarea
                            value={config.key_concepts}
                            onChange={(e) => setConfig(prev => ({ ...prev, key_concepts: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                            rows={3}
                            placeholder="Enter key concepts..."
                            aria-label="Key Concepts"
                            title="Key Concepts"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300">
                            Scene Description
                          </label>
                          <textarea
                            value={config.scene_description || ''}
                            onChange={(e) => setConfig(prev => ({ ...prev, scene_description: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                            rows={3}
                            placeholder="Enter a detailed description of the scene..."
                            aria-label="Scene Description"
                            title="Scene Description"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300">
                            Education Level
                          </label>
                          <select
                            value={config.education_level}
                            onChange={(e) => setConfig(prev => ({ ...prev, education_level: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                            aria-label="Education Level"
                            title="Education Level"
                          >
                            <option value="Elementary">Elementary</option>
                            <option value="Middle School">Middle School</option>
                            <option value="High School">High School</option>
                            <option value="College">College</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300">
                            Learning Objectives
                          </label>
                          <textarea
                            value={config.learning_objectives}
                            onChange={(e) => setConfig(prev => ({ ...prev, learning_objectives: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                            rows={3}
                            placeholder="Enter learning objectives..."
                            aria-label="Learning Objectives"
                            title="Learning Objectives"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300">
                            Interactive Features
                          </label>
                          <textarea
                            value={config.interactive_features}
                            onChange={(e) => setConfig(prev => ({ ...prev, interactive_features: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                            rows={3}
                            placeholder="Enter interactive features..."
                            aria-label="Interactive Features"
                            title="Interactive Features"
                          />
                        </div>

                        {/* Components Section */}
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Components
                          </label>
                          {config.components.map((component, index) => (
                            <div key={index} className="flex gap-2 mb-2">
                              <input
                                type="text"
                                value={component.component_name}
                                onChange={(e) => {
                                  const newComponents = [...config.components];
                                  newComponents[index] = { ...component, component_name: e.target.value };
                                  setConfig(prev => ({ ...prev, components: newComponents }));
                                }}
                                placeholder="Component Name"
                                className="flex-1 rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                              />
                              <input
                                type="text"
                                value={component.component_description}
                                onChange={(e) => {
                                  const newComponents = [...config.components];
                                  newComponents[index] = { ...component, component_description: e.target.value };
                                  setConfig(prev => ({ ...prev, components: newComponents }));
                                }}
                                placeholder="Description"
                                className="flex-1 rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                              />
                              <button
                                onClick={() => {
                                  const newComponents = config.components.filter((_, i) => i !== index);
                                  setConfig(prev => ({ ...prev, components: newComponents }));
                                }}
                                className="px-2 py-1 text-red-400 hover:text-red-300"
                              >
                                Remove
                              </button>
                            </div>
                          ))}
                          <button
                            onClick={() => {
                              setConfig(prev => ({
                                ...prev,
                                components: [...prev.components, { component_name: '', component_description: '' }]
                              }));
                            }}
                            className="mt-2 text-sm text-purple-400 hover:text-purple-300"
                          >
                            + Add Component
                          </button>
                        </div>

                        {/* Materials Section */}
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Materials
                          </label>
                          {config.materials.map((material, index) => (
                            <div key={index} className="flex gap-4 mb-4 items-end bg-gray-800 p-3 rounded-lg">
                              <div className="flex-1">
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`material-name-${index}`}>Material Name</label>
                                <input
                                  id={`material-name-${index}`}
                                  type="text"
                                  value={material.material_name}
                                  onChange={(e) => {
                                    const newMaterials = [...config.materials];
                                    newMaterials[index] = { ...material, material_name: e.target.value };
                                    setConfig(prev => ({ ...prev, materials: newMaterials }));
                                  }}
                                  placeholder="Material Name"
                                  className="w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                                />
                              </div>
                              <div className="flex-1">
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`material-type-${index}`}>Material Type</label>
                                <select
                                  id={`material-type-${index}`}
                                  value={material.material_type || ''}
                                  onChange={(e) => {
                                    const newMaterials = [...config.materials];
                                    newMaterials[index] = { ...material, material_type: e.target.value };
                                    setConfig(prev => ({ ...prev, materials: newMaterials }));
                                  }}
                                  className="w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                                >
                                  <option value="">Select Type</option>
                                  <option value="MeshStandardMaterial">Standard Material</option>
                                  <option value="MeshPhysicalMaterial">Physical Material</option>
                                  <option value="MeshBasicMaterial">Basic Material</option>
                                  <option value="MeshPhongMaterial">Phong Material</option>
                                  <option value="MeshLambertMaterial">Lambert Material</option>
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`material-color-${index}`}>Material Color</label>
                                <input
                                  id={`material-color-${index}`}
                                  type="color"
                                  value={material.color || "#ffffff"}
                                  onChange={(e) => {
                                    const newMaterials = [...config.materials];
                                    newMaterials[index] = { ...material, color: e.target.value };
                                    setConfig(prev => ({ ...prev, materials: newMaterials }));
                                  }}
                                  className="w-10 h-10 rounded border-gray-700 bg-gray-900"
                                  aria-label="Material Color"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`material-metalness-${index}`}>Material Metalness</label>
                                <input
                                  id={`material-metalness-${index}`}
                                  type="range"
                                  min="0"
                                  max="1"
                                  step="0.1"
                                  value={material.metalness}
                                  onChange={(e) => {
                                    const newMaterials = [...config.materials];
                                    newMaterials[index] = { ...material, metalness: parseFloat(e.target.value) };
                                    setConfig(prev => ({ ...prev, materials: newMaterials }));
                                  }}
                                  className="w-24"
                                  aria-label="Material Metalness"
                                />
                                <span className="ml-2 text-xs text-gray-300">{material.metalness}</span>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`material-roughness-${index}`}>Material Roughness</label>
                                <input
                                  id={`material-roughness-${index}`}
                                  type="range"
                                  min="0"
                                  max="1"
                                  step="0.1"
                                  value={material.roughness}
                                  onChange={(e) => {
                                    const newMaterials = [...config.materials];
                                    newMaterials[index] = { ...material, roughness: parseFloat(e.target.value) };
                                    setConfig(prev => ({ ...prev, materials: newMaterials }));
                                  }}
                                  className="w-24"
                                  aria-label="Material Roughness"
                                />
                                <span className="ml-2 text-xs text-gray-300">{material.roughness}</span>
                              </div>
                              <button
                                onClick={() => {
                                  const newMaterials = config.materials.filter((_, i) => i !== index);
                                  setConfig(prev => ({ ...prev, materials: newMaterials }));
                                }}
                                className="px-2 py-1 text-red-400 hover:text-red-300 text-xs border border-red-400 rounded"
                              >
                                Remove
                              </button>
                            </div>
                          ))}
                          <button
                            onClick={() => {
                              setConfig(prev => ({
                                ...prev,
                                materials: [...prev.materials, { material_name: '', material_type: '', color: '#808080', metalness: 0.5, roughness: 0.5 }]
                              }));
                            }}
                            className="mt-2 text-sm text-purple-400 hover:text-purple-300"
                          >
                            + Add Material
                          </button>
                        </div>

                        {/* Lights Section */}
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Lights
                          </label>
                          {config.lights.map((light, index) => (
                            <div key={index} className="flex gap-4 mb-4 items-end bg-gray-800 p-3 rounded-lg">
                              <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`light-type-${index}`}>Light Type</label>
                                <select
                                  id={`light-type-${index}`}
                                  value={light.light_type}
                                  onChange={(e) => {
                                    const newLights = [...config.lights];
                                    newLights[index] = { 
                                      ...light, 
                                      light_type: e.target.value,
                                      light_class: e.target.value 
                                    };
                                    setConfig(prev => ({ ...prev, lights: newLights }));
                                  }}
                                  className="w-32 rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                                >
                                  <option value="AmbientLight">Ambient</option>
                                  <option value="DirectionalLight">Directional</option>
                                  <option value="Point">Point</option>
                                  <option value="Spot">Spot</option>
                                  <option value="HemisphereLight">Hemisphere</option>
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`light-color-${index}`}>Light Color</label>
                                <input
                                  id={`light-color-${index}`}
                                  type="color"
                                  value={light.light_color || "#ffffff"}
                                  onChange={(e) => {
                                    const newLights = [...config.lights];
                                    newLights[index] = { ...light, light_color: e.target.value };
                                    setConfig(prev => ({ ...prev, lights: newLights }));
                                  }}
                                  className="w-10 h-10 rounded border-gray-700 bg-gray-900"
                                  aria-label="Light Color"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1" htmlFor={`light-intensity-${index}`}>Light Intensity</label>
                                <input
                                  id={`light-intensity-${index}`}
                                  type="range"
                                  min="0"
                                  max="2"
                                  step="0.1"
                                  value={light.intensity}
                                  onChange={(e) => {
                                    const newLights = [...config.lights];
                                    newLights[index] = { ...light, intensity: parseFloat(e.target.value) };
                                    setConfig(prev => ({ ...prev, lights: newLights }));
                                  }}
                                  className="w-24"
                                  aria-label="Light Intensity"
                                />
                                <span className="ml-2 text-xs text-gray-300">{light.intensity}</span>
                              </div>
                              <button
                                onClick={() => {
                                  const newLights = config.lights.filter((_, i) => i !== index);
                                  setConfig(prev => ({ ...prev, lights: newLights }));
                                }}
                                className="px-2 py-1 text-red-400 hover:text-red-300 text-xs border border-red-400 rounded"
                              >
                                Remove
                              </button>
                            </div>
                          ))}
                          <button
                            onClick={() => {
                              setConfig(prev => ({
                                ...prev,
                                lights: [...prev.lights, { 
                                  light_type: 'AmbientLight', 
                                  light_class: 'AmbientLight',
                                  light_color: '#ffffff', 
                                  intensity: 1.0 
                                }]
                              }));
                            }}
                            className="mt-2 text-sm text-purple-400 hover:text-purple-300"
                          >
                            + Add Light
                          </button>
                        </div>

                        {/* Renderer Settings */}
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Renderer Settings
                          </label>
                          <div className="mt-2 space-y-2">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={config?.renderer?.antialias ?? true}
                                onChange={(e) => setConfig(prev => ({
                                  ...prev,
                                  renderer: { ...prev.renderer, antialias: e.target.checked }
                                }))}
                                className="h-4 w-4 rounded border-gray-700 bg-gray-900 text-purple-600 focus:ring-purple-500"
                              />
                              <label className="ml-2 text-sm text-gray-300">Antialiasing</label>
                            </div>
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={config?.renderer?.shadowMapEnabled ?? true}
                                onChange={(e) => setConfig(prev => ({
                                  ...prev,
                                  renderer: { ...prev.renderer, shadowMapEnabled: e.target.checked }
                                }))}
                                className="h-4 w-4 rounded border-gray-700 bg-gray-900 text-purple-600 focus:ring-purple-500"
                              />
                              <label className="ml-2 text-sm text-gray-300">Shadows</label>
                            </div>
                          </div>
                        </div>

                        {/* Animation Settings */}
                        <div>
                          <label className="block text-sm font-medium text-gray-300">
                            Animation Speed
                          </label>
                          <input
                            type="number"
                            value={config.animation_speed}
                            onChange={(e) => setConfig(prev => ({ ...prev, animation_speed: parseFloat(e.target.value) }))}
                            className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                            step="0.1"
                            min="0.1"
                            max="5"
                          />
                        </div>

                        {/* TTS Settings */}
                        <div className="space-y-2">
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Text-to-Speech Settings
                          </label>
                          <div className="grid grid-cols-3 gap-4">
                            <div>
                              <label className="block text-xs text-gray-400">Language</label>
                              <select
                                value={config.tts_language}
                                onChange={(e) => setConfig(prev => ({ ...prev, tts_language: e.target.value }))}
                                className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                              >
                                <option value="en-US">English (US)</option>
                                <option value="en-GB">English (UK)</option>
                                <option value="es-ES">Spanish</option>
                                <option value="fr-FR">French</option>
                                <option value="de-DE">German</option>
                              </select>
                            </div>
                            <div>
                              <label className="block text-xs text-gray-400">Rate</label>
                              <input
                                type="number"
                                value={config.tts_rate}
                                onChange={(e) => setConfig(prev => ({ ...prev, tts_rate: parseFloat(e.target.value) }))}
                                className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                                step="0.1"
                                min="0.5"
                                max="2"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-gray-400">Pitch</label>
                              <input
                                type="number"
                                value={config.tts_pitch}
                                onChange={(e) => setConfig(prev => ({ ...prev, tts_pitch: parseFloat(e.target.value) }))}
                                className="mt-1 block w-full rounded-md border-gray-700 bg-gray-900 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                                step="0.1"
                                min="0.5"
                                max="2"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Narration Texts */}
                        <div className="space-y-4">
                          <h4 className="text-md font-medium">Narration Texts</h4>
                          
                          {/* Intro Narration */}
                          <div className="space-y-2">
                            <h5 className="text-sm font-medium text-gray-300">Introduction</h5>
                            {config.intro_narration_texts.map((text, index) => (
                              <div key={`intro-${index}`} className="flex space-x-2">
                                <input
                                  type="text"
                                  value={text}
                                  onChange={(e) => updateNarrationText('intro_narration_texts', index, e.target.value)}
                                  className="flex-1 px-3 py-2 bg-gray-700 rounded-md text-white"
                                  placeholder="Enter introduction text"
                                />
                                <button
                                  onClick={() => removeNarrationText('intro_narration_texts', index)}
                                  className="px-3 py-2 bg-red-600 hover:bg-red-700 rounded-md text-white"
                                >
                                  Remove
                                </button>
                              </div>
                            ))}
                            <button
                              onClick={() => addNarrationText('intro_narration_texts', '')}
                              className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-md text-white"
                            >
                              Add Introduction Text
                            </button>
                          </div>

                          {/* Supporting Narration */}
                          <div className="space-y-2">
                            <h5 className="text-sm font-medium text-gray-300">Supporting Information</h5>
                            {config.supporting_narration_texts.map((text, index) => (
                              <div key={`support-${index}`} className="flex space-x-2">
                                <input
                                  type="text"
                                  value={text}
                                  onChange={(e) => updateNarrationText('supporting_narration_texts', index, e.target.value)}
                                  className="flex-1 px-3 py-2 bg-gray-700 rounded-md text-white"
                                  placeholder="Enter supporting text"
                                />
                                <button
                                  onClick={() => removeNarrationText('supporting_narration_texts', index)}
                                  className="px-3 py-2 bg-red-600 hover:bg-red-700 rounded-md text-white"
                                >
                                  Remove
                                </button>
                              </div>
                            ))}
                            <button
                              onClick={() => addNarrationText('supporting_narration_texts', '')}
                              className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-md text-white"
                            >
                              Add Supporting Text
                            </button>
                          </div>
                        </div>
                      </Disclosure.Panel>
                    </>
                  )}
                </Disclosure>

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

                  {/* Show retrieval button only in development mode */}
                  {process.env.NODE_ENV === 'development' && (
                    <button
                      onClick={handleRetrieveSimilar}
                      disabled={loading}
                      className={`flex-1 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-pink-600 hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500 ${
                        loading ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {loading ? 'Retrieving...' : 'Show Retrieval Results'}
                    </button>
                  )}

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
                    <div className="flex space-x-4">
                      <button
                        onClick={handleSaveToLibrary}
                        className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
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
                            d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                          />
                        </svg>
                        Add to Library
                      </button>
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

              {html && (
                <div className="mt-4 space-y-4">
                  <div className="flex justify-between items-center">
                    <button
                      onClick={() => setShowConfig(!showConfig)}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-md text-white font-medium transition-colors"
                    >
                      {showConfig ? "Hide Configuration" : "Show Configuration"}
                    </button>
                    <button
                      onClick={handleRegenerate}
                      disabled={regenerating}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md text-white font-medium transition-colors disabled:opacity-50"
                    >
                      {regenerating ? "Regenerating..." : "Regenerate"}
                    </button>
                  </div>

                  {showConfig && (
                    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
                      <h3 className="text-lg font-semibold mb-4">Visualization Configuration</h3>
                      
                      {/* Renderer Settings */}
                      <div className="space-y-2">
                        <h4 className="text-md font-medium">Renderer Settings</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="antialias"
                              checked={config.renderer.antialias}
                              onChange={(e) => setConfig(prev => ({
                                ...prev,
                                renderer: { ...prev.renderer, antialias: e.target.checked }
                              }))}
                              className="rounded border-gray-700 bg-gray-900 text-purple-600 focus:ring-purple-500"
                            />
                            <label htmlFor="antialias">Antialiasing</label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="shadowMapEnabled"
                              checked={config.renderer.shadowMapEnabled}
                              onChange={(e) => setConfig(prev => ({
                                ...prev,
                                renderer: { ...prev.renderer, shadowMapEnabled: e.target.checked }
                              }))}
                              className="rounded border-gray-700 bg-gray-900 text-purple-600 focus:ring-purple-500"
                            />
                            <label htmlFor="shadowMapEnabled">Shadows</label>
                          </div>
                        </div>
                      </div>

                      {/* Animation Speed */}
                      <div className="space-y-2">
                        <h4 className="text-md font-medium">Animation Speed</h4>
                        <input
                          type="range"
                          min="0.1"
                          max="2"
                          step="0.1"
                          value={config.animation_speed}
                          onChange={(e) => setConfig(prev => ({
                            ...prev,
                            animation_speed: parseFloat(e.target.value)
                          }))}
                          className="w-full"
                        />
                        <div className="text-sm text-gray-400">
                          Speed: {config.animation_speed}x
                        </div>
                      </div>

                      {/* Tone Mapping Exposure */}
                      <div className="space-y-2">
                        <h4 className="text-md font-medium">Tone Mapping Exposure</h4>
                        <input
                          type="range"
                          min="0.1"
                          max="2"
                          step="0.1"
                          value={config.renderer.toneMappingExposure}
                          onChange={(e) => setConfig(prev => ({
                            ...prev,
                            renderer: { ...prev.renderer, toneMappingExposure: parseFloat(e.target.value) }
                          }))}
                          className="w-full"
                        />
                        <div className="text-sm text-gray-400">
                          Exposure: {config.renderer.toneMappingExposure}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 