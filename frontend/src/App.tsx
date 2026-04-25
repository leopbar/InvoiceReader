import React from 'react';
import { createBrowserRouter, RouterProvider, Link, useLocation, Navigate, Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Receipt, Archive, Upload, Users, LogOut, Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';

import UploadPage from './pages/UploadPage';
import HistoryPage from './pages/HistoryPage';
import InvoiceDetailPage from './pages/InvoiceDetailPage';
import LoginPage from './pages/LoginPage';
import UserManagementPage from './pages/UserManagementPage';

function Navigation() {
  const location = useLocation();
  const path = location.pathname;
  const { user, isAdmin, signOut } = useAuth();

  return (
    <nav className="bg-white border-b shadow-sm sticky top-0 z-10 w-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg text-white">
              <Receipt size={24} />
            </div>
            <span className="font-bold text-xl text-gray-900 tracking-tight">Invoice Reader</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <Link 
              to="/" 
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                path === '/' ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
              }`}
            >
              <Upload size={18} />
              <span>Upload</span>
            </Link>
            <Link 
              to="/history" 
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                path.startsWith('/history') || path.startsWith('/invoice') ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
              }`}
            >
              <Archive size={18} />
              <span>History</span>
            </Link>

            {isAdmin && (
              <Link 
                to="/users" 
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  path.startsWith('/users') ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                <Users size={18} />
                <span>Users</span>
              </Link>
            )}

            <div className="pl-4 ml-2 border-l border-gray-200 flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-600 truncate max-w-[150px]">
                {user?.email}
              </span>
              <button
                onClick={signOut}
                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                title="Sign Out"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function Layout() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="animate-spin text-blue-500" size={48} />
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-slate-50 relative pb-12">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <Outlet />
      </main>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        path: "/",
        element: <UploadPage />,
      },
      {
        path: "/history",
        element: <HistoryPage />,
      },
      {
        path: "/invoice/:id",
        element: <InvoiceDetailPage />,
      },
      {
        path: "/users",
        element: <UserManagementPage />,
      },
    ],
  },
]);

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-center" />
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
