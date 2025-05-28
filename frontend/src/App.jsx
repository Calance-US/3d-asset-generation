import React, { useState } from 'react';

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("openai");
  const [html, setHtml] = useState("");

  async function handleGenerate() {
    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, provider })
      });
      const data = await res.text();
      setHtml(data);
    } catch (err) {
      setHtml(`<p style="color:red;">Error generating scene: ${err.message}</p>`);
    }
  }

  return (
    <div className="p-6 space-y-4 max-w-4xl mx-auto font-sans">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">3D Concept Visualizer</h1>

      <label className="block text-sm font-medium text-gray-700">
        Enter Concept Prompt
      </label>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        className="w-full h-28 p-3 border border-gray-300 rounded shadow-sm focus:ring focus:ring-blue-200"
        placeholder="e.g., 'Explain Ohm's Law using a 3D electric circuit'"
      />

      <label className="block text-sm font-medium text-gray-700 mt-2">
        Choose AI Provider
      </label>
      <select
        value={provider}
        onChange={(e) => setProvider(e.target.value)}
        className="p-2 border border-gray-300 rounded shadow-sm"
      >
        <option value="openai">OpenAI (GPT-4)</option>
        <option value="ollama">Ollama (local)</option>
        <option value="anthropic">Anthropic (Claude)</option>
      </select>

      <button
        onClick={handleGenerate}
        className="px-6 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 mt-4"
      >
        Generate Scene
      </button>

      {html && (
        <div className="mt-6">
          <iframe
            title="3D Scene"
            className="w-full h-[600px] border rounded shadow"
            srcDoc={html}
            sandbox="allow-scripts allow-same-origin"
          ></iframe>
        </div>
      )}
    </div>
  );
}
