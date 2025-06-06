import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Generator from './components/Generator';
import Admin from './components/Admin';

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("openai");
  const [subject, setSubject] = useState("physics");
  const [html, setHtml] = useState("");
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const iframeRef = useRef(null);

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

  async function loadHistory() {
    try {
      const res = await fetch("http://localhost:8000/history");
      const data = await res.json();
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
      const blob = new Blob([entry.html], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date(entry.timestamp).toISOString().split('T')[0];
      const filename = `visualization_${timestamp}_${entry.prompt.slice(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase()}.html`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Error downloading file: ${err.message}`);
    }
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Generator />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </Router>
  );
}
