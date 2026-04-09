import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Trash2, Plus, Loader2, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';
import { getUsers, createUser, deleteUser } from '../services/api';

export default function UserManagementPage() {
  const { isAdmin, user } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('user');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
    }
  }, [isAdmin]);

  const fetchUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (e) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await createUser(newEmail, newPassword, newRole);
      toast.success('User created successfully');
      setShowModal(false);
      setNewEmail('');
      setNewPassword('');
      setNewRole('user');
      fetchUsers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setCreating(false);
    }
  };

  const handleRemoveUser = async (targetId: string, email: string) => {
    if (targetId === user?.id) {
      toast.error("You cannot remove yourself");
      return;
    }
    
    if (window.confirm(`Are you sure you want to completely remove ${email}? This action cannot be undone.`)) {
      try {
        await deleteUser(targetId);
        toast.success(`User ${email} removed`);
        fetchUsers();
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to remove user');
      }
    }
  };

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-red-500">
        <ShieldAlert size={60} className="mb-4" />
        <h2 className="text-2xl font-bold">Access Denied</h2>
        <p className="text-gray-500 mt-2">You must be an administrator to view this page.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-500 mt-1">Manage system administrators and standard users.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition shadow-sm"
        >
          <Plus size={16} />
          <span>Add User</span>
        </button>
      </div>

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="flex justify-center p-12">
            <Loader2 className="animate-spin text-blue-500" size={30} />
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4 font-semibold text-gray-700 text-sm">Email</th>
                <th className="px-6 py-4 font-semibold text-gray-700 text-sm">Role</th>
                <th className="px-6 py-4 font-semibold text-gray-700 text-sm">Created Date</th>
                <th className="px-6 py-4 font-semibold text-gray-700 text-sm w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map(u => (
                <tr key={u.user_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-800">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => handleRemoveUser(u.user_id, u.email)}
                      disabled={u.user_id === user?.id}
                      className="text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:hover:text-gray-400 transition-colors tooltip"
                      title={u.user_id === user?.id ? "Cannot delete yourself" : "Remove user"}
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b bg-gray-50 flex justify-between items-center">
              <h3 className="font-bold text-gray-900">Add New User</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-700">&times;</button>
            </div>
            <form onSubmit={handleAddUser} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                <input 
                  type="email" required
                  value={newEmail} onChange={e => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Temporary Password</label>
                <input 
                  type="password" required minLength={6}
                  value={newPassword} onChange={e => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select 
                  value={newRole} onChange={e => setNewRole(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option value="user">User</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
              <div className="pt-4 flex justify-end space-x-3 border-t mt-6">
                <button 
                  type="button" onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button 
                  type="submit" disabled={creating}
                  className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? <Loader2 size={16} className="animate-spin mr-2"/> : null}
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
