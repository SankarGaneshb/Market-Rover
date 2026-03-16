import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import PromoterProfile from './pages/PromoterProfile.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col font-sans">
        <Navbar />
        <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/promoter/:symbol" element={<PromoterProfile />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
