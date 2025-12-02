"use client";

import React, { useState } from 'react';
import { Users, MapPin, MessageSquare, BarChart3, Settings, FileText, Shield, Search, Plus, Edit, Trash2, Eye, Check, X, AlertCircle, TrendingUp, Leaf, Award } from 'lucide-react';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');

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
  const dashboardStats = [
    { label: 'Total Users', value: '12,543', change: '+12%', icon: Users, color: 'bg-blue-500' },
    { label: 'Active Destinations', value: '284', change: '+5%', icon: MapPin, color: 'bg-green-500' },
    { label: 'Pending Reviews', value: '45', change: '-15%', icon: MessageSquare, color: 'bg-orange-500' },
    { label: 'Eco Impact Score', value: '8,542', change: '+28%', icon: Leaf, color: 'bg-emerald-500' },
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

  const users = [
    { id: 1, username: 'johndoe', email: 'john@example.com', role: 'Customer', status: 'Active', ecoPoints: 150, joinDate: '2024-01-15', lastActivity: '2024-11-26' },
    { id: 2, username: 'janesmith', email: 'jane@example.com', role: 'Admin', status: 'Active', ecoPoints: 320, joinDate: '2024-02-20', lastActivity: '2024-11-25' },
    { id: 3, username: 'mikejohnson', email: 'mike@example.com', role: 'Customer', status: 'Suspended', ecoPoints: 85, joinDate: '2024-03-10', lastActivity: '2024-11-20' },
    { id: 4, username: 'sarahw', email: 'sarah@example.com', role: 'Customer', status: 'Banned', ecoPoints: 0, joinDate: '2024-04-05', lastActivity: '2024-10-15' },
  ];

  const destinations = [
    { id: 101, name: 'Bali Eco Resort', country: 'Indonesia', ecoRating: 4.8, verified: true, tags: ['Sustainable', 'Wildlife Protection', 'Green Energy'], createdDate: '2024-01-10' },
    { id: 102, name: 'Amazon Rainforest Lodge', country: 'Brazil', ecoRating: 4.9, verified: true, tags: ['Carbon Neutral', 'Conservation', 'Local Community'], createdDate: '2024-02-15' },
    { id: 103, name: 'Glacier National Park', country: 'USA', ecoRating: 4.6, verified: false, tags: ['Nature Preserve', 'Low Impact'], createdDate: '2024-03-20' },
  ];

  const reviews = [
    { id: 1, user: 'johndoe', destination: 'Bali Eco Resort', rating: 5, comment: 'Amazing sustainable resort! The solar panels and recycling program were impressive.', status: 'Pending', botFlag: 'Safe', submittedDate: '2024-11-25' },
    { id: 2, user: 'janesmith', destination: 'Amazon Lodge', rating: 4, comment: 'Great experience, but transportation could be improved.', status: 'Pending', botFlag: 'Safe', submittedDate: '2024-11-24' },
    { id: 3, user: 'suspicious_user', destination: 'Costa Rica', rating: 1, comment: 'Terrible! Click here for better deals: fake-website.com', status: 'Pending', botFlag: 'Spam Detected', submittedDate: '2024-11-23' },
    { id: 4, user: 'sarahw', destination: 'Iceland Tour', rating: 5, comment: 'Absolutely breathtaking landscapes and eco-friendly practices!', status: 'Approved', botFlag: 'Safe', submittedDate: '2024-11-22' },
  ];

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
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStats.map((stat, index) => (
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
      if (userFilter === 'suspended') return user.status === 'Suspended';
      return true;
    });

    return (
    <div className="space-y-6">
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
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select 
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Users</option>
              <option value="suspended">Only Suspended</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Eco Points</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Activity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{user.username}</p>
                      <p className="text-xs text-gray-500">ID: {user.id}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{user.email}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        user.role === 'Admin' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {user.role}
                      </span>
                      <button className={`flex items-center gap-1 px-2 py-1 text-xs rounded ${
                        user.role === 'Admin' 
                          ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' 
                          : 'bg-purple-600 text-white hover:bg-purple-700'
                      }`} title={user.role === 'Admin' ? 'Remove Admin' : 'Make Admin'}>
                        <Shield className="w-3 h-3" />
                        {user.role === 'Admin' ? 'Remove' : 'Make Admin'}
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      user.status === 'Active' ? 'bg-green-100 text-green-800' :
                      user.status === 'Suspended' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{user.ecoPoints}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{user.lastActivity}</td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button className="text-blue-600 hover:text-blue-800" title="View Activity">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="text-green-600 hover:text-green-800" title="Add Eco Points">
                        <Plus className="w-4 h-4" />
                      </button>
                      <button className={`${user.status === 'Suspended' ? 'text-green-600 hover:text-green-800' : 'text-yellow-600 hover:text-yellow-800'}`} title={user.status === 'Suspended' ? 'Unsuspend' : 'Suspend'}>
                        <AlertCircle className="w-4 h-4" />
                      </button>
                      <button className="text-red-600 hover:text-red-800" title="Ban User">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* User Activity Modal Placeholder */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> Click the eye icon to view detailed user activity including login history, bookings, reviews, and eco-friendly actions.
        </p>
      </div>
    </div>
    );
  };

  // Render Destinations
  const [destinationFilter, setDestinationFilter] = useState('all');

  const renderDestinations = () => {
    const filteredDestinations = destinations.filter(dest => {
      if (destinationFilter === 'verified') return dest.verified === true;
      if (destinationFilter === 'unverified') return dest.verified === false;
      return true;
    });

    return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col gap-4 mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Destinations</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name or ID..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select 
              value={destinationFilter}
              onChange={(e) => setDestinationFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Destinations</option>
              <option value="verified">Only Green-Verified</option>
              <option value="unverified">Only Non-Verified</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Eco Rating</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Verified</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Environmental Tags</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredDestinations.map((dest) => (
                <tr key={dest.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-mono text-gray-900">{dest.id}</td>
                  <td className="px-6 py-4">
                    <p className="text-sm font-medium text-gray-900">{dest.name}</p>
                    <p className="text-xs text-gray-500">{dest.createdDate}</p>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{dest.country}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1">
                      <Leaf className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-semibold text-gray-900">{dest.ecoRating}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <button className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                      dest.verified 
                        ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}>
                      {dest.verified ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                      {dest.verified ? 'Verified' : 'Unverified'}
                    </button>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {dest.tags.map((tag, index) => (
                        <span key={index} className="px-2 py-1 bg-emerald-100 text-emerald-800 text-xs rounded-full">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button className="text-blue-600 hover:text-blue-800" title="Edit">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="text-red-600 hover:text-red-800" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
    );
  };

  // Render Review Moderation
  const renderReviewModeration = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Review Moderation</h2>
          <div className="flex gap-2">
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
              {reviews.filter(r => r.status === 'Pending').length} Pending
            </span>
            <span className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-full">
              {reviews.filter(r => r.botFlag !== 'Safe').length} Flagged
            </span>
          </div>
        </div>

        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className={`border rounded-lg p-4 ${
              review.botFlag !== 'Safe' ? 'border-red-300 bg-red-50' : 'border-gray-200'
            }`}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <p className="font-medium text-gray-900">{review.user}</p>
                    <span className="text-sm text-gray-500">→ {review.destination}</span>
                    <div className="flex items-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <span key={i} className={i < review.rating ? 'text-yellow-400' : 'text-gray-300'}>★</span>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">Submitted: {review.submittedDate}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    review.status === 'Approved' ? 'bg-green-100 text-green-800' :
                    review.status === 'Rejected' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {review.status}
                  </span>
                  {review.botFlag !== 'Safe' && (
                    <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {review.botFlag}
                    </span>
                  )}
                </div>
              </div>

              <p className="text-sm text-gray-700 mb-3">{review.comment}</p>

              {review.status === 'Pending' && (
                <div className="flex gap-2">
                  <button className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                    <Check className="w-4 h-4" />
                    Approve
                  </button>
                  <button className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700">
                    <X className="w-4 h-4" />
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">🤖 Auto-Moderation Bot</h3>
        <p className="text-sm text-blue-800">
          The content moderation bot automatically pre-checks all reviews for spam, inappropriate content, and suspicious links. 
          Flagged reviews are highlighted in red for your immediate attention.
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