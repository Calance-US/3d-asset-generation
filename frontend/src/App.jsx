import React from "react";
import Generator from "./components/Generator";
import Admin from "./components/Admin";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-900 text-white">
        <Routes>
          <Route path="/" element={<Generator />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
