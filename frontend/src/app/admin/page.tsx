"use client";

import React, { useState, useEffect } from 'react';
import { Users, MapPin, MessageSquare, BarChart3, Settings, FileText, Shield, Search, Plus, Edit, Trash2, Eye, Check, X, AlertCircle, TrendingUp, Leaf, Award, RefreshCw, ExternalLink, Bot, Copy } from 'lucide-react';
import { api, AdminUserResponse, ReviewResponse, Mission, DestinationWithCertificate, GreenVerifiedStatus } from '@/lib/api';
import { useRouter } from 'next/navigation';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Check if user is admin
  useEffect(() => {
    const userRole = localStorage.getItem('user_role');
    if (userRole !== 'Admin') {
      alert('Access denied. Admin privileges required.');
      router.push('/home');
    }
  }, [router]);

  // State for real data
  const [users, setUsers] = useState<AdminUserResponse[]>([]);
  const [reviews, setReviews] = useState<ReviewResponse[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [destinations, setDestinations] = useState<DestinationWithCertificate[]>([]);
  const [reviewStatuses, setReviewStatuses] = useState<{[key: string]: 'pending' | 'approved' | 'rejected'}>({});
  const [dashboardStats, setDashboardStats] = useState({
    total_users: 0,
    active_destinations: 0,
    pending_reviews: 0,
    eco_impact_score: 0,
  });

  // Fetch users
  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    }
  }, [activeTab]);

  // Fetch reviews
  useEffect(() => {
    if (activeTab === 'reviews') {
      fetchReviews();
    }
  }, [activeTab]);

  // Fetch destinations
  useEffect(() => {
    if (activeTab === 'destinations') {
      fetchDestinations();
    }
  }, [activeTab]);

  // Fetch dashboard data
  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboardData();
    }
  }, [activeTab]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const fetchedUsers = await api.listAllUsers({ limit: 100 });
      setUsers(fetchedUsers);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const fetchedReviews = await api.getAllReviews();
      setReviews(fetchedReviews);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch reviews');
      console.error('Error fetching reviews:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDestinations = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedDestinations = await api.adminGetAllDestinations({ limit: 500 });
      setDestinations(fetchedDestinations);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch destinations');
      console.error('Error fetching destinations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // Fetch all users to calculate stats
      const allUsers = await api.listAllUsers({ limit: 1000 });
      const allReviews = await api.getAllReviews();
      
      setDashboardStats({
        total_users: allUsers.length,
        active_destinations: 0, // This would need a dedicated endpoint
        pending_reviews: allReviews.length,
        eco_impact_score: allUsers.reduce((sum, user) => sum + (user.eco_point || 0), 0),
      });
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard data');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await api.adminDeleteUser(userId);
      alert('User deleted successfully');
      fetchUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to delete user');
    }
  };

  const handleChangePassword = async (userId: number, username: string) => {
    const newPassword = prompt(`Enter new password for ${username}:`);
    if (!newPassword || newPassword.length < 6) {
      alert('Password must be at least 6 characters');
      return;
    }
    
    try {
      await api.adminUpdatePassword(userId, newPassword);
      alert('Password updated successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to update password');
    }
  };

  const handleChangeStatus = (userId: number, username: string) => {
    const newStatus = prompt(`Enter new status for ${username} (Active/Suspended/Banned):`);
    if (!newStatus) return;
    // TODO: Implement status change API
    alert('Status change feature - to be implemented with backend API');
  };

  const handleChangeRole = async (userId: number, currentRole: string, username: string) => {
    const newRole = currentRole === 'Admin' ? 'User' : 'Admin';
    if (!confirm(`Change ${username}'s role to ${newRole}?`)) return;
    
    try {
      await api.adminUpdateRole(userId, newRole);
      alert('Role updated successfully');
      fetchUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to update role');
    }
  };

  const handleDeleteReview = async (destinationId: string) => {
    if (!confirm('Are you sure you want to delete this review?')) return;
    
    try {
      await api.deleteReview(destinationId);
      alert('Review deleted successfully');
      fetchReviews();
    } catch (err: any) {
      alert(err.message || 'Failed to delete review');
    }
  };

  //TODO: Implement approve/reject review with backend API
  const handleApproveReview = (reviewKey: string) => {
    setReviewStatuses(prev => ({ ...prev, [reviewKey]: 'approved' }));
    alert('Review approved! (Frontend only - no backend support)');
  };

  const handleRejectReview = (reviewKey: string) => {
    setReviewStatuses(prev => ({ ...prev, [reviewKey]: 'rejected' }));
    alert('Review rejected! (Frontend only - no backend support)');
  };

  const getReviewStatus = (reviewKey: string) => {
    return reviewStatuses[reviewKey] || 'pending';
  };

  // Certificate management handlers
  const handleManualCertificateChange = async (destinationId: string, currentStatus: GreenVerifiedStatus) => {
    const statusOptions: GreenVerifiedStatus[] = ['Green Certified', 'Not Green Verified', 'AI Green Verified'];
    const statusChoice = prompt(
      `Current status: ${currentStatus}\n\nChoose new status:\n1. Green Certified\n2. Not Green Verified\n3. AI Green Verified\n\nEnter 1, 2, or 3:`
    );
    
    if (!statusChoice) return;
    
    const statusIndex = parseInt(statusChoice) - 1;
    if (statusIndex < 0 || statusIndex >= statusOptions.length) {
      alert('Invalid choice');
      return;
    }
    
    const newStatus = statusOptions[statusIndex];
    
    try {
      setLoading(true);
      await api.adminUpdateCertificate(destinationId, newStatus);
      alert(`Certificate updated to: ${newStatus}`);
      fetchDestinations();
    } catch (err: any) {
      alert(err.message || 'Failed to update certificate');
    } finally {
      setLoading(false);
    }
  };

  const handleExternalApiCheck = async (destinationId: string) => {
    if (!confirm('Run external API verification check for this destination?')) return;
    
    try {
      setLoading(true);
      const result = await api.adminCheckExternalApi(destinationId);
      
      if (result.passed) {
        const shouldUpdate = confirm(
          `External API Check PASSED ✓\n\nScore: ${(result.score! * 100).toFixed(1)}%\n${result.details}\n\nUpdate certificate to "Green Certified"?`
        );
        if (shouldUpdate) {
          await api.adminUpdateCertificate(destinationId, 'Green Certified');
          fetchDestinations();
        }
      } else {
        alert(
          `External API Check FAILED ✗\n\nScore: ${(result.score! * 100).toFixed(1)}%\n${result.details}`
        );
      }
    } catch (err: any) {
      alert(err.message || 'Failed to run external API check');
    } finally {
      setLoading(false);
    }
  };

  const handleAiCheck = async (destinationId: string) => {
    if (!confirm('Run AI verification check for this destination?')) return;
    
    try {
      setLoading(true);
      const result = await api.adminCheckAiVerification(destinationId);
      
      if (result.verified) {
        const shouldUpdate = confirm(
          `AI Verification PASSED ✓\n\nConfidence: ${(result.confidence! * 100).toFixed(1)}%\nGreen Score: ${(result.green_score! * 100).toFixed(1)}%\n\nUpdate certificate to "AI Green Verified"?`
        );
        if (shouldUpdate) {
          await api.adminUpdateCertificate(destinationId, 'AI Green Verified');
          fetchDestinations();
        }
      } else {
        alert(
          `AI Verification FAILED ✗\n\nConfidence: ${(result.confidence! * 100).toFixed(1)}%\nGreen Score: ${(result.green_score! * 100).toFixed(1)}%`
        );
      }
    } catch (err: any) {
      alert(err.message || 'Failed to run AI check');
    } finally {
      setLoading(false);
    }
  };

  // Sidebar Navigation
  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
    { id: 'users', name: 'User Management', icon: Users },
    { id: 'destinations', name: 'Destinations', icon: MapPin },
    { id: 'reviews', name: 'Review Moderation', icon: MessageSquare },
    { id: 'audit', name: 'Audit Logs', icon: FileText },
    { id: 'settings', name: 'Settings', icon: Settings },
  ];

  // Mock data
  const dashboardStatsDisplay = [
    { label: 'Total Users', value: dashboardStats.total_users.toString(), change: '+12%', icon: Users, color: 'bg-blue-500' },
    { label: 'Active Destinations', value: dashboardStats.active_destinations.toString(), change: '+5%', icon: MapPin, color: 'bg-green-500' },
    { label: 'Pending Reviews', value: dashboardStats.pending_reviews.toString(), change: '-15%', icon: MessageSquare, color: 'bg-orange-500' },
    { label: 'Eco Impact Score', value: dashboardStats.eco_impact_score.toLocaleString(), change: '+28%', icon: Leaf, color: 'bg-emerald-500' },
  ];

  const popularDestinations = [
    { id: 1, name: 'Bali, Indonesia', visits: 4523, ecoRating: 4.8, growth: '+15%' },
    { id: 2, name: 'Costa Rica', visits: 3892, ecoRating: 4.9, growth: '+22%' },
    { id: 3, name: 'Iceland', visits: 3654, ecoRating: 4.7, growth: '+18%' },
    { id: 4, name: 'New Zealand', visits: 3201, ecoRating: 4.6, growth: '+12%' },
  ];

  const userGrowth = [
    { month: 'Jan', users: 8500 },
    { month: 'Feb', users: 9200 },
    { month: 'Mar', users: 9800 },
    { month: 'Apr', users: 10500 },
    { month: 'May', users: 11200 },
    { month: 'Jun', users: 12543 },
  ];

  // Removed mock users and destinations arrays - now using state from API

  const auditLogs = [
    { id: 1, admin: 'admin@travel.com', action: 'User Suspended', target: 'mikejohnson (ID: 3)', timestamp: '2024-11-26 10:30:15', details: 'Suspended for policy violation' },
    { id: 2, admin: 'admin@travel.com', action: 'Destination Verified', target: 'Bali Eco Resort (ID: 101)', timestamp: '2024-11-26 09:15:22', details: 'Verified eco credentials' },
    { id: 3, admin: 'admin@travel.com', action: 'Review Rejected', target: 'Review ID: 3', timestamp: '2024-11-25 16:45:30', details: 'Spam content detected' },
    { id: 4, admin: 'admin@travel.com', action: 'User Made Admin', target: 'janesmith (ID: 2)', timestamp: '2024-11-25 14:20:10', details: 'Role changed from Customer to Admin' },
    { id: 5, admin: 'admin@travel.com', action: 'Eco Points Added', target: 'johndoe (ID: 1)', timestamp: '2024-11-24 11:05:45', details: 'Added 50 eco points' },
  ];

  // Render Dashboard
  const renderDashboard = () => (
    <div className="space-y-6">
      {loading && <div className="text-center py-4">Loading dashboard data...</div>}
      {error && <div className="bg-red-100 text-red-800 p-4 rounded">{error}</div>}
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStatsDisplay.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className={`text-sm mt-1 ${stat.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.change} from last month
                </p>
              </div>
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Popular Destinations */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Popular Destinations
          </h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {popularDestinations.map((dest) => (
              <div key={dest.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4">
                  <MapPin className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="font-medium text-gray-900">{dest.name}</p>
                    <p className="text-sm text-gray-600">{dest.visits} visits this month</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="flex items-center gap-1">
                      <Leaf className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-900">{dest.ecoRating}</span>
                    </div>
                    <p className="text-xs text-gray-600">Eco Rating</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-green-600">{dest.growth}</p>
                    <p className="text-xs text-gray-600">Growth</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Growth Chart */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">User Growth</h2>
        </div>
        <div className="p-6">
          <div className="flex items-end justify-between h-48 gap-4">
            {userGrowth.map((data, index) => (
              <div key={index} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full bg-blue-500 rounded-t-lg hover:bg-blue-600 transition-colors" 
                     style={{ height: `${(data.users / 12543) * 100}%` }}></div>
                <p className="text-xs text-gray-600">{data.month}</p>
                <p className="text-xs font-semibold text-gray-900">{data.users}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Eco Impact Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg shadow p-6 text-white">
          <Award className="w-8 h-8 mb-3 opacity-80" />
          <p className="text-3xl font-bold">2,847</p>
          <p className="text-sm opacity-90 mt-1">Carbon Offset (tons)</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg shadow p-6 text-white">
          <Leaf className="w-8 h-8 mb-3 opacity-80" />
          <p className="text-3xl font-bold">156</p>
          <p className="text-sm opacity-90 mt-1">Eco-Certified Destinations</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg shadow p-6 text-white">
          <Users className="w-8 h-8 mb-3 opacity-80" />
          <p className="text-3xl font-bold">8,542</p>
          <p className="text-sm opacity-90 mt-1">Community Eco Points</p>
        </div>
      </div>
    </div>
  );

  // Render User Management
  const [userFilter, setUserFilter] = useState('all');
  
  const renderUserManagement = () => {
    const filteredUsers = users.filter(user => {
      if (userFilter === 'suspended') return user.role === 'Suspended';
      if (searchTerm) {
        return user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
               user.email.toLowerCase().includes(searchTerm.toLowerCase());
      }
      return true;
    });

    return (
    <div className="space-y-6">
      {loading && <div className="text-center py-4">Loading users...</div>}
      {error && <div className="bg-red-100 text-red-800 p-4 rounded">{error}</div>}
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col gap-4 mb-6">
          <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
            </div>
            <select 
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            >
              <option value="all">All Users</option>
              <option value="suspended">Only Suspended</option>
            </select>
            <button 
              onClick={fetchUsers}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{user.username}</p>
                        <p className="text-xs text-gray-500">ID: {user.id}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{user.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        user.role === 'Admin' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                        {user.rank}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                        Active
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleChangeRole(user.id, user.role || 'User', user.username)}
                          className="text-purple-600 hover:text-purple-800" 
                          title="Change Role"
                        >
                          <Shield className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleChangeStatus(user.id, user.username)}
                          className="text-yellow-600 hover:text-yellow-800" 
                          title="Change Status"
                        >
                          <AlertCircle className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleChangePassword(user.id, user.username)}
                          className="text-blue-600 hover:text-blue-800" 
                          title="Change Password"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDeleteUser(user.id)}
                          className="text-red-600 hover:text-red-800" 
                          title="Delete User"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* User Activity Modal Placeholder */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> User management is now connected to the backend API. You can manage roles, status, passwords, and delete users.
        </p>
      </div>
    </div>
    );
  };

  // Render Destinations
  const [destinationFilter, setDestinationFilter] = useState<'all' | GreenVerifiedStatus>('all');

  const renderDestinations = () => {
    const filteredDestinations = destinations.filter(dest => {
      if (destinationFilter === 'all') return true;
      return dest.green_verified === destinationFilter;
    });

    const getStatusBadgeColor = (status: GreenVerifiedStatus) => {
      switch (status) {
        case 'Green Certified':
          return 'bg-green-100 text-green-800';
        case 'AI Green Verified':
          return 'bg-blue-100 text-blue-800';
        case 'Not Green Verified':
        default:
          return 'bg-gray-100 text-gray-800';
      }
    };

    return (
    <div className="space-y-6">
      {loading && <div className="text-center py-4">Loading destinations...</div>}
      {error && <div className="bg-red-100 text-red-800 p-4 rounded">{error}</div>}
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Destination Certificate Management</h2>
            <button 
              onClick={fetchDestinations}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by place ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
            </div>
            <select 
              value={destinationFilter}
              onChange={(e) => setDestinationFilter(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            >
              <option value="all">All Destinations</option>
              <option value="Green Certified">Green Certified</option>
              <option value="AI Green Verified">AI Green Verified</option>
              <option value="Not Green Verified">Not Green Verified</option>
            </select>
          </div>
          <div className="text-sm text-gray-600">
            Total: {filteredDestinations.length} destinations
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Place ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Certificate Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredDestinations
                .filter(dest => !searchTerm || dest.place_id.toLowerCase().includes(searchTerm.toLowerCase()))
                .map((dest) => (
                <tr key={dest.place_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-mono text-gray-900 truncate max-w-xs" title={dest.place_id}>
                        {dest.place_id.length > 30 ? `${dest.place_id.substring(0, 30)} ...` : dest.place_id}
                      </p>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(dest.place_id);
                          alert('Place ID copied to clipboard!');
                        }}
                        className="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="Copy full Place ID"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(dest.green_verified)}`}>
                      {dest.green_verified}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleManualCertificateChange(dest.place_id, dest.green_verified)}
                        className="flex items-center gap-1 px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
                        title="Manually Change Certificate"
                      >
                        <Edit className="w-3 h-3" />
                        Manual
                      </button>
                      <button 
                        onClick={() => handleExternalApiCheck(dest.place_id)}
                        className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                        title="Check with External API"
                      >
                        <ExternalLink className="w-3 h-3" />
                        API Check
                      </button>
                      <button 
                        onClick={() => handleAiCheck(dest.place_id)}
                        className="flex items-center gap-1 px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                        title="AI Verification Check"
                      >
                        <Bot className="w-3 h-3" />
                        AI Check
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Certificate Management:</strong> You can manually change certificates, check with external APIs (mock), or run AI verification (mock). 
          The actual API and AI endpoints will be connected when backend is ready.
        </p>
      </div>
    </div>
    );
  };

  // Render Review Moderation
  const renderReviewModeration = () => (
    <div className="space-y-6">
      {loading && <div className="text-center py-4">Loading reviews...</div>}
      {error && <div className="bg-red-100 text-red-800 p-4 rounded">{error}</div>}
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Review Moderation</h2>
          <div className="flex gap-2">
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
              {reviews.length} Total Reviews
            </span>
            <button 
              onClick={fetchReviews}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {reviews.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No reviews found</div>
          ) : (
            reviews.map((review) => {
              const reviewKey = `${review.user_id}-${review.destination_id}`;
              const status = getReviewStatus(reviewKey);
              return (
              <div key={review.destination_id} className="border rounded-lg p-4 border-gray-200">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <p className="font-medium text-gray-900">User ID: {review.user_id}</p>
                      <span className="text-sm text-gray-500">→ {review.destination_id}</span>
                      <div className="flex items-center gap-1">
                        {[...Array(5)].map((_, i) => (
                          <span key={i} className={i < review.rating ? 'text-yellow-400' : 'text-gray-300'}>★</span>
                        ))}
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        status === 'approved' ? 'bg-green-100 text-green-800' :
                        status === 'rejected' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">Submitted: {new Date(review.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {review.files_urls && review.files_urls.length > 0 && (
                      <span className="text-xs text-blue-600">{review.files_urls.length} files</span>
                    )}
                  </div>
                </div>

                <p className="text-sm text-gray-700 mb-3">{review.content}</p>

                {review.files_urls && review.files_urls.length > 0 && (
                  <div className="flex gap-2 mb-3">
                    {review.files_urls.slice(0, 3).map((url, idx) => (
                      <img 
                        key={idx} 
                        src={url} 
                        alt={`Review image ${idx + 1}`}
                        className="w-20 h-20 object-cover rounded"
                      />
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  {status === 'pending' && (
                    <>
                      <button 
                        onClick={() => handleApproveReview(reviewKey)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                      >
                        <Check className="w-4 h-4" />
                        Approve
                      </button>
                      <button 
                        onClick={() => handleRejectReview(reviewKey)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
                      >
                        <X className="w-4 h-4" />
                        Reject
                      </button>
                    </>
                  )}
                  <button 
                    onClick={() => handleDeleteReview(review.destination_id)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            );
            })
          )}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">📋 Review Moderation</h3>
        <p className="text-sm text-blue-800">
          Reviews are fetched from the backend API. You can approve, reject, or delete reviews.
          <strong> Note:</strong> Approve/Reject actions are frontend-only simulations - the backend doesn't support review status updates yet.
        </p>
      </div>
    </div>
  );

  // Render Audit Logs
  const renderAuditLogs = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Audit Logs</h2>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Search className="w-4 h-4" />
            Filter
          </button>
        </div>

        <div className="space-y-3">
          {auditLogs.map((log) => (
            <div key={log.id} className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
              <div className="mt-1">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Shield className="w-4 h-4 text-blue-600" />
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between mb-1">
                  <p className="font-medium text-gray-900">{log.action}</p>
                  <span className="text-xs text-gray-500">{log.timestamp}</span>
                </div>
                <p className="text-sm text-gray-600 mb-1">
                  Target: <span className="font-medium">{log.target}</span>
                </p>
                <p className="text-xs text-gray-500">{log.details}</p>
                <p className="text-xs text-gray-400 mt-1">By: {log.admin}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h3 className="font-semibold text-purple-900 mb-2">📋 Audit Trail</h3>
        <p className="text-sm text-purple-800">
          All administrative actions are logged and tracked. This includes user management, content moderation, 
          verification changes, and system modifications. Logs are retained for compliance and security purposes.
        </p>
      </div>
    </div>
  );

  // Render Settings
  const renderSettings = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">System Settings</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Auto-Moderation Bot</p>
              <p className="text-sm text-gray-600">Automatically flag suspicious reviews</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Email Notifications</p>
              <p className="text-sm text-gray-600">Send alerts for pending reviews</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Require Verification</p>
              <p className="text-sm text-gray-600">New destinations need admin approval</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        </div>
        <nav className="p-4">
          {navigation.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors ${
                activeTab === item.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'users' && renderUserManagement()}
        {activeTab === 'destinations' && renderDestinations()}
        {activeTab === 'reviews' && renderReviewModeration()}
        {activeTab === 'audit' && renderAuditLogs()}
        {activeTab === 'settings' && renderSettings()}
      </div>
    </div>
  );
};

export default AdminDashboard;