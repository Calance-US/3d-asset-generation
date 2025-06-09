import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';

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
  const navigate = useNavigate();

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      const response = await fetch("http://localhost:8000/admin/prompts");
      if (response.ok) {
        const data = await response.json();
        setPrompts(data.prompts);
      } else {
        setError("Failed to load prompts");
      }
    } catch (err) {
      setError("Error connecting to server");
    } finally {
      setLoading(false);
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

  const handleDelete = async (promptId) => {
    try {
      const response = await fetch(`http://localhost:8000/admin/prompts/${promptId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setPrompts(prompts.filter(prompt => prompt.id !== promptId));
      } else {
        setError("Failed to delete prompt");
      }
    } catch (err) {
      setError("Error connecting to server");
    }
  };

  const truncateContent = (content) => {
    // Remove markdown syntax for preview
    const plainText = content.replace(/[#*`_~\[\]]/g, '');
    return plainText.length > 150 ? plainText.substring(0, 150) + '...' : plainText;
  };

  if (loading) {
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