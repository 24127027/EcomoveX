"use client";

import React, { useState, useEffect } from 'react';
import { ChevronLeft, MapPin, Clock, Tag, Star, Bookmark, Home, Map, CalendarDays, Send, User } from 'lucide-react';
import { PlaceDetails, PlaceDataCategory, api } from '@/lib/api';
import { useSearchParams } from 'next/navigation';

// Missing descriptions 

const PlaceDetailPage = () => {
  const [placeDetails, setPlaceDetails] = useState<PlaceDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'home' | 'track' | 'planning' | 'ticket' | 'user'>('home');
  const [showAllImages, setShowAllImages] = useState(false);
  const [showAllReviews, setShowAllReviews] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [reviewText, setReviewText] = useState('');
  const [userRating, setUserRating] = useState(0);
  const [showFullDescription, setShowFullDescription] = useState(false);

  const searchParams = useSearchParams();
  const place_id = searchParams.get("place_id") || "";

  useEffect(() => {
    loadPlaceDetails();
  }, []);

  const loadPlaceDetails = async () => {
    try {
      const placeDetails = await api.getPlaceDetails(place_id, null, ["basic", "contact", "atmosphere"]);
      setPlaceDetails(placeDetails);
    }
    catch (error) {
      console.error('Error fetching place details:', error);
    }
    setLoading(false);
  };

  const handleSubmitReview = () => {
    if (reviewText.trim() && userRating > 0) {
      alert('Review submitted! (API not implemented yet)');
      setReviewText('');
      setUserRating(0);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!placeDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Place not found</p>
      </div>
    );
  }

  const displayPhotos = (placeDetails.photos || []).slice(0, 4);
  const displayReviews = (placeDetails.reviews || []).slice(0, 2);

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-green-600 text-white px-4 py-4 flex items-center justify-between sticky top-0 z-10">
        <button className="p-1" onClick={() => window.history.back()}>
          <ChevronLeft size={24} />
        </button>
        <h1 className="text-lg font-medium flex-1 text-center mx-4">
          {placeDetails.name}
        </h1>
        <button 
          className="p-1"
          onClick={() => setIsBookmarked(!isBookmarked)}
        >
          <Bookmark size={24} fill={isBookmarked ? 'white' : 'none'} />
        </button>
      </div>

      {/* Full Screen Image Gallery Modal */}
      {showAllImages && (
        <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
          <div className="bg-green-600 text-white px-4 py-4 flex items-center sticky top-0 z-10">
            <button className="p-1" onClick={() => setShowAllImages(false)}>
              <ChevronLeft size={24} />
            </button>
            <h1 className="text-lg font-medium flex-1 text-center mx-4">
              All Images - {placeDetails.name}
            </h1>
            <div className="w-10"></div>
          </div>
          <div className="grid grid-cols-2 gap-2 p-4 pb-20">
            {placeDetails.photos?.map((photo, index) => (
              <img
                key={index}
                src={photo.photo_url}
                alt={`Place ${index + 1}`}
                className="w-full h-40 object-cover rounded-lg"
              />
            ))}
          </div>
        </div>
      )}

      {/* Full Screen Reviews Modal */}
      {showAllReviews && (
        <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
          <div className="bg-green-600 text-white px-4 py-4 flex items-center sticky top-0 z-10">
            <button className="p-1" onClick={() => setShowAllReviews(false)}>
              <ChevronLeft size={24} />
            </button>
            <h1 className="text-lg font-medium flex-1 text-center mx-4">
              All Reviews - {placeDetails.name}
            </h1>
            <div className="w-10"></div>
          </div>
          
          <div className="p-4 pb-20">
            {/* Leave Review Form */}
            <div className="mb-4 pb-4 border-b border-gray-200 bg-white rounded-lg p-4 shadow-sm">
              <p className="text-sm text-gray-700 mb-2">Leave your review</p>
              <div className="flex gap-1 mb-3">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setUserRating(star)}
                    className="p-0"
                  >
                    <Star
                      size={20}
                      fill={star <= userRating ? '#FFC107' : 'none'}
                      stroke={star <= userRating ? '#FFC107' : '#D1D5DB'}
                    />
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Write something about your feeling at this place..."
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button
                  onClick={handleSubmitReview}
                  className="p-2 bg-green-600 text-white rounded-lg"
                  disabled={!reviewText.trim() || userRating === 0}
                >
                  <Send size={18} />
                </button>
              </div>
            </div>

            {/* All Review List */}
            <div className="space-y-3">
              {placeDetails.reviews?.map((review) => (
                <div key={review.id} className="bg-green-50 rounded-lg p-3">
                  <div className="flex items-start gap-2 mb-2">
                    <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                      <User size={16} className="text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-800 text-sm">{review.userName}</p>
                      {review.userName === 'You' && (
                        <button className="text-green-600 text-xs">Edit</button>
                      )}
                    </div>
                  </div>
                  <p className="text-gray-700 text-xs leading-relaxed ml-10">
                    {review.comment}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Breadcrumb */}
      <div className="px-4 py-2 bg-white text-xs text-gray-500 flex items-center gap-1">
        <Home size={12} />
        <span>&gt;</span>
        <span className="text-gray-700">Lạc trình/hội</span>
      </div>

      {/* Notification Banner */}
      <div className="mx-4 my-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-blue-700 font-medium text-sm mb-2">Notification</h3>
        <p className="text-blue-600 text-xs leading-relaxed">
          Heads up! This café serve all drinks in single-use cups — even when you stay. Feel free to bring your own tumbler and show some love for our planet.
        </p>
      </div>

      {/* Main Content */}
      <div className="bg-white mx-4 rounded-lg shadow-sm p-4 mb-4">
        {/* Address */}
        <div className="mb-4">
          <div className="flex items-start gap-2 text-sm">
            <MapPin size={16} className="text-gray-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-700 mb-1">Address:</p>
              <p className="text-gray-600">{placeDetails.formatted_address}</p>
            </div>
          </div>
        </div>

        {/* Opening Hours */}
        <div className="mb-4">
          <div className="flex items-start gap-2 text-sm">
            <Clock size={16} className="text-gray-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-700 mb-1">Open hour:</p>
                {placeDetails.opening_hours?.weekday_text ? (
                <ul className="text-gray-600 text-xs">
                  {placeDetails.opening_hours.weekday_text.map((text, idx) => (
                  <li key={idx}>{text}</li>
                  ))}
                </ul>
                ) : (
                <p className="text-gray-600">{placeDetails.opening_hours ? (placeDetails.opening_hours.open_now ? 'Open now' : 'Closed now') : 'N/A'}</p>
                )}
            </div>
          </div>
        </div>

        {/* Category */}
        <div className="mb-4">
          <div className="flex items-start gap-2 text-sm">
            <Tag size={16} className="text-gray-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-700 mb-1">Category:</p>
              <p className="text-gray-600">{placeDetails.types.join(', ')}</p>
            </div>
          </div>
        </div>

        {/* Green Level */}
        <div className="mb-4">
          <p className="font-medium text-gray-700 text-sm mb-2">Green Level:</p>
          <span className="inline-block bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-medium">
            {placeDetails.sustainable_certified? 'Sustainably Certified' : 'Not Certified'}
          </span>
        </div>

        {/* Price Range */}
        {placeDetails.price_level && (
          <div className="mb-4">
            <p className="font-medium text-gray-700 text-sm mb-1">Price:</p>
            <p className="text-gray-600 text-sm">{placeDetails.price_level}</p>
          </div>
        )}

        {/* Description */}
        {/* {placeDetails.description && (
          <div className="mb-4">
            <p className="font-medium text-gray-700 text-sm mb-2">Description:</p>
            <p className={`text-gray-600 text-xs leading-relaxed whitespace-pre-line ${!showFullDescription ? 'line-clamp-3' : ''}`}>
              {placeDetails.description}
            </p>
            <button 
              onClick={() => setShowFullDescription(!showFullDescription)}
              className="text-green-600 text-xs mt-2"
            >
              {showFullDescription ? 'See less <' : 'See more >'}
            </button>
          </div>
        )} */}
      </div>

      {/* Images Section */}
      <div className="bg-white mx-4 rounded-lg shadow-sm p-4 mb-4">
        <h3 className="font-medium text-gray-800 mb-3">Images</h3>
        <div className="grid grid-cols-2 gap-2">
          {displayPhotos.map((photo, index) => (
            <img
              key={index}
              src={photo.photo_url}
              alt={`Place ${index + 1}`}
              className="w-full h-32 object-cover rounded-lg"
            />
          ))}
        </div>
        {placeDetails.photos && placeDetails.photos.length > 4 && (
          <button
            onClick={() => setShowAllImages(true)}
            className="text-green-600 text-sm mt-3 block text-right w-full"
          >
            View all ({placeDetails.photos.length}) images &gt;
          </button>
        )}
      </div>

      {/* Reviews Section */}
      <div className="bg-white mx-4 rounded-lg shadow-sm p-4 mb-4">
        <h3 className="font-medium text-gray-800 mb-3">Reviews</h3>
        
        {/* Leave Review Form */}
        <div className="mb-4 pb-4 border-b border-gray-200">
          <p className="text-sm text-gray-700 mb-2">Leave your review</p>
          <div className="flex gap-1 mb-3">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setUserRating(star)}
                className="p-0"
              >
                <Star
                  size={20}
                  fill={star <= userRating ? '#FFC107' : 'none'}
                  stroke={star <= userRating ? '#FFC107' : '#D1D5DB'}
                />
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Write something about your feeling at this place..."
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <button
              onClick={handleSubmitReview}
              className="p-2 bg-green-600 text-white rounded-lg"
              disabled={!reviewText.trim() || userRating === 0}
            >
              <Send size={18} />
            </button>
          </div>
        </div>

        {/* Review List */}
        <div className="space-y-3">
          {displayReviews.map((review) => (
            <div key={review.id} className="bg-green-50 rounded-lg p-3">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                  <User size={16} className="text-gray-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-800 text-sm">{review.userName}</p>
                  {review.userName === 'You' && (
                    <button className="text-green-600 text-xs">Edit</button>
                  )}
                </div>
              </div>
              <p className="text-gray-700 text-xs leading-relaxed ml-10">
                {review.comment}
              </p>
            </div>
          ))}
        </div>

        {placeDetails.reviews && placeDetails.reviews.length > 2 && (
          <button
            onClick={() => setShowAllReviews(true)}
            className="text-green-600 text-sm mt-3 block text-right w-full"
          >
            View all reviews &gt;
          </button>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-6 py-3">
        <div className="flex justify-between items-center max-w-md mx-auto">
          <button
            onClick={() => setActiveTab('home')}
            className={`flex flex-col items-center gap-1 ${
              activeTab === 'home' ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            <Home size={24} fill={activeTab === 'home' ? 'currentColor' : 'none'} />
            <span className="text-xs">Home</span>
          </button>
          <button
            onClick={() => setActiveTab('track')}
            className={`flex flex-col items-center gap-1 ${
              activeTab === 'track' ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            <Map size={24} />
            <span className="text-xs">Track</span>
          </button>
          <button
            onClick={() => setActiveTab('planning')}
            className={`flex flex-col items-center gap-1 ${
              activeTab === 'planning' ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            <CalendarDays size={24} />
            <span className="text-xs">Planning</span>
          </button>
          <button
            onClick={() => setActiveTab('ticket')}
            className={`flex flex-col items-center gap-1 ${
              activeTab === 'ticket' ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            <Tag size={24} />
            <span className="text-xs">Ticket</span>
          </button>
          <button
            onClick={() => setActiveTab('user')}
            className={`flex flex-col items-center gap-1 ${
              activeTab === 'user' ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            <User size={24} />
            <span className="text-xs">User</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default PlaceDetailPage;