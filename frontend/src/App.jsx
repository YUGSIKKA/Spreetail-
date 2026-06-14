import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Group from './pages/Group';
import Expenses from './pages/Expenses';
import Import from './pages/Import';
import ImportReport from './pages/ImportReport';

// Dynamic route guard components to check auth on mount/render
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

function AnonymousRoute({ children }) {
  const token = localStorage.getItem('token');
  return !token ? children : <Navigate to="/" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Routes>
          <Route 
            path="/login" 
            element={
              <AnonymousRoute>
                <Login />
              </AnonymousRoute>
            } 
          />
          <Route 
            path="/register" 
            element={
              <AnonymousRoute>
                <Register />
              </AnonymousRoute>
            } 
          />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/group/:id" 
            element={
              <ProtectedRoute>
                <Group />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/expenses" 
            element={
              <ProtectedRoute>
                <Expenses />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/import" 
            element={
              <ProtectedRoute>
                <Import />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/import/report/:id" 
            element={
              <ProtectedRoute>
                <ImportReport />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
