"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ChevronLeft,
  Star,
  Heart,
  Camera,
  X,
  AlertCircle,
  Plus,
  Send,
  Leaf,
} from "lucide-react";
import { Jost, Roboto } from "next/font/google";
import { api, PlaceDetails, ReviewResponse } from "@/lib/api";

// --- FONTS ---
const roboto = Roboto({
  subsets: ["vietnamese"],
  weight: ["400", "500", "700"],
});
const jost = Jost({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

// ... (Các Component con: NotificationBox, RatingStars, ReviewItem giữ nguyên như cũ) ...
const NotificationBox = ({ text }: { text: string }) => (
  <div className="bg-blue-50 border border-blue-100 border-dashed rounded-xl p-4 mb-6 relative overflow-hidden">
    <div className="absolute top-0 right-0 w-16 h-16 bg-blue-100 rounded-bl-full -mr-8 -mt-8 opacity-50"></div>
    <div className="flex gap-3 relative z-10">
      <div className="bg-blue-100 p-2 rounded-full h-fit text-blue-600">
        <AlertCircle size={20} />
      </div>
      <div>
        <h4
          className={`${jost.className} text-blue-700 font-bold text-sm mb-1`}
        >
          Eco Notification
        </h4>
        <p className="text-blue-600 text-xs leading-relaxed font-medium">
          {text}
        </p>
      </div>
    </div>
  </div>
);

const RatingStars = ({
  rating,
  setRating,
  interactive = false,
  size = 16,
}: {
  rating: number;
  setRating?: (r: number) => void;
  interactive?: boolean;
  size?: number;
}) => {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          size={size}
          className={`${
            star <= rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
          } ${
            interactive
              ? "cursor-pointer hover:scale-110 transition-transform"
              : ""
          }`}
          onClick={() => interactive && setRating && setRating(star)}
        />
      ))}
    </div>
  );
};

const ReviewItem = ({
  review,
  isMe,
}: {
  review: ReviewResponse;
  isMe: boolean;
}) => (
  <div className="bg-[#F9FFF9] border border-green-50 p-4 rounded-2xl mb-3 shadow-sm">
    <div className="flex justify-between items-start mb-2">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden border border-white shadow-sm">
          <div className="w-full h-full flex items-center justify-center bg-green-100 text-green-600 font-bold text-sm">
            {isMe ? "Me" : "U"}
          </div>
        </div>
        <div>
          <p className={`${jost.className} font-bold text-gray-800 text-sm`}>
            {isMe ? "You" : `User #${review.user_id}`}
          </p>
          <RatingStars rating={review.rating} size={12} />
        </div>
      </div>
      {isMe && (
        <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">
          Your Review
        </span>
      )}
    </div>
    <p
      className={`${roboto.className} text-gray-600 text-sm leading-relaxed mb-3`}
    >
      {review.content}
    </p>
    {review.files_urls && review.files_urls.length > 0 && (
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {review.files_urls.map((url, idx) => (
          <img
            key={idx}
            src={url}
            alt="review"
            className="w-20 h-20 object-cover rounded-lg border border-gray-100 shrink-0"
          />
        ))}
      </div>
    )}
    <p className="text-gray-400 text-[10px] text-right mt-1">
      {new Date(review.created_at).toLocaleDateString()}
    </p>
  </div>
);

// --- MAIN PAGE ---
export default function PlaceDetailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const placeId = searchParams.get("place_id");

  const [place, setPlace] = useState<PlaceDetails | null>(null);
  const [reviews, setReviews] = useState<ReviewResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for Saving Destination
  const [isSaved, setIsSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // State for Logic mở rộng
  const [isExpandedInfo, setIsExpandedInfo] = useState(false);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);

  // State for Add Review Modal
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [newRating, setNewRating] = useState(5);
  const [newComment, setNewComment] = useState("");
  const [reviewImages, setReviewImages] = useState<File[]>([]);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);

  // 1. Fetch Data
  useEffect(() => {
    const fetchData = async () => {
      if (!placeId) return;
      try {
        setLoading(true);

        // Fetch User Info
        try {
          const me = await api.getUserProfile();
          setCurrentUser(me);
        } catch (e) {
          console.log("Not logged in");
        }

        // Fetch Place & Reviews
        const [placeData, reviewsData] = await Promise.all([
          api.getPlaceDetails(placeId, null, [
            "basic",
            "contact",
            "atmosphere",
          ]),
          api.getReviewsByDestination(placeId).catch(() => []),
        ]);

        setPlace(placeData);
        setReviews(reviewsData);

        // --- CHECK SAVED STATUS (Logic mới) ---
        try {
          const savedList = await api.getSavedDestinations();
          // Kiểm tra xem placeId hiện tại có trong danh sách đã lưu không
          const exists = savedList.some(
            (item) => item.destination_id === placeId
          );
          setIsSaved(exists);
        } catch (e) {
          console.error("Failed to check saved status", e);
        }
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Could not load place details.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [placeId]);

  const handleToggleSave = async () => {
    if (!placeId || isSaving) return;

    const previousState = isSaved;
    setIsSaved(!previousState);
    setIsSaving(true);

    try {
      if (previousState) {
        await api.unsaveDestination(placeId);
        console.log("Unsaved");
      } else {
        await api.saveDestination(placeId);
        console.log("Saved");
      }
    } catch (error) {
      console.error("Toggle save failed:", error);
      setIsSaved(previousState);
      alert("Failed to update heart status.");
    } finally {
      setIsSaving(false);
    }
  };

  // ... (Các hàm handleImageUpload, removeImage, submitReview GIỮ NGUYÊN) ...
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setReviewImages((prev) => [...prev, ...files]);
    }
  };

  const removeImage = (index: number) => {
    setReviewImages((prev) => prev.filter((_, i) => i !== index));
  };

  const submitReview = async () => {
    if (!placeId) return;
    setIsSubmittingReview(true);
    try {
      await api.createReview(
        placeId,
        {
          rating: newRating,
          content: newComment,
        },
        reviewImages
      );

      const updatedReviews = await api.getReviewsByDestination(placeId);
      setReviews(updatedReviews);

      setIsReviewModalOpen(false);
      setNewComment("");
      setNewRating(5);
      setReviewImages([]);
      alert("Review posted successfully!");
    } catch (err) {
      console.error("Failed to post review:", err);
      alert("Failed to post review. Please try again.");
    } finally {
      setIsSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#53B552]"></div>
      </div>
    );
  }

  if (error || !place) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
        <p className="text-gray-500 mb-4">{error || "Place not found"}</p>
        <button
          onClick={() => router.back()}
          className="text-[#53B552] font-bold hover:underline"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex justify-center">
      <div className="w-full max-w-md bg-white min-h-screen shadow-xl relative pb-20">
        {/* HEADER */}
        <div className="bg-[#53B552] px-4 py-4 sticky top-0 z-30 shadow-md flex items-center justify-between text-white">
          <button
            onClick={() => router.back()}
            className="p-1 hover:bg-white/20 rounded-full transition-colors"
          >
            <ChevronLeft size={24} />
          </button>

          <h1 className={`${jost.className} font-bold text-lg truncate px-2`}>
            {place.name}
          </h1>

          <button
            onClick={handleToggleSave}
            disabled={isSaving}
            className="p-1 hover:bg-white/20 rounded-full transition-colors"
          >
            <Heart
              size={24}
              className={isSaved ? "fill-white text-white" : "text-white"}
            />
          </button>
        </div>

        <div className="p-5 space-y-6">
          <NotificationBox text="Heads up! This place serves all drinks in reusable cups. Feel free to bring your own tumbler to get a 10% discount!" />

          {/* INFO SECTION */}
          <div className="space-y-4">
            <div className="flex gap-4 items-start">
              <span
                className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
              >
                Address.
              </span>
              <p className="text-gray-600 text-sm leading-tight">
                {place.formatted_address}
              </p>
            </div>

            <div className="flex gap-4 items-start">
              <span
                className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
              >
                Open hour.
              </span>
              <p className="text-gray-600 text-sm">07:30 - 22:30</p>
            </div>

            <div className="flex gap-4 items-start">
              <span
                className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
              >
                Category.
              </span>
              <p className="text-gray-600 text-sm capitalize">
                {place.types?.[0]?.replace(/_/g, " ") || "Place"}
              </p>
            </div>

            <div className="flex gap-4 items-center">
              <span
                className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
              >
                Green Level.
              </span>
              <span className="bg-yellow-100 text-yellow-700 text-xs px-3 py-1 rounded-full font-bold flex items-center gap-1 border border-yellow-200">
                <Leaf size={12} className="fill-current" />
                AI Green Verified
              </span>
            </div>

            {isExpandedInfo && (
              <div className="animate-in fade-in slide-in-from-top-2 duration-300 space-y-4 pt-4 border-t border-dashed border-gray-100 mt-4">
                {place.website && (
                  <div className="flex gap-4 items-start">
                    <span
                      className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
                    >
                      Website.
                    </span>
                    <a
                      href={place.website}
                      target="_blank"
                      className="text-[#53B552] text-sm underline truncate block flex-1"
                    >
                      {place.website}
                    </a>
                  </div>
                )}

                {place.formatted_phone_number && (
                  <div className="flex gap-4 items-start">
                    <span
                      className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
                    >
                      Phone.
                    </span>
                    <p className="text-gray-600 text-sm">
                      {place.formatted_phone_number}
                    </p>
                  </div>
                )}

                <div className="flex gap-4 items-center">
                  <span
                    className={`${jost.className} w-24 font-bold text-gray-900 shrink-0`}
                  >
                    Rating.
                  </span>
                  <div className="flex items-center gap-1">
                    <span className="text-gray-900 font-bold text-sm">
                      {place.rating}
                    </span>
                    <Star
                      size={12}
                      className="fill-yellow-400 text-yellow-400"
                    />
                    <span className="text-gray-400 text-xs">
                      ({place.user_ratings_total} reviews)
                    </span>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={() => setIsExpandedInfo(!isExpandedInfo)}
              className="w-full text-right text-xs text-gray-400 underline mt-2 hover:text-[#53B552]"
            >
              {isExpandedInfo ? "Show less" : "View details →"}
            </button>
          </div>

          <hr className="border-gray-100 border-dashed" />

          {/* IMAGES GRID */}
          <div>
            <h3
              className={`${jost.className} font-bold text-gray-900 text-lg mb-3`}
            >
              Images
            </h3>
            <div className="grid grid-cols-2 gap-2 rounded-2xl overflow-hidden h-64">
              {place.photos && place.photos.length > 0 ? (
                place.photos.slice(0, 4).map((photo, index) => (
                  <div
                    key={index}
                    className={`relative overflow-hidden bg-gray-100 ${
                      index === 0 && place.photos!.length >= 3
                        ? "row-span-2 h-full"
                        : "h-32"
                    }`}
                  >
                    <img
                      src={photo.photo_url}
                      alt="Place"
                      className="w-full h-full object-cover hover:scale-110 transition-transform duration-500"
                    />
                  </div>
                ))
              ) : (
                <div className="col-span-2 h-full bg-gray-100 flex items-center justify-center text-gray-400">
                  No images available
                </div>
              )}
            </div>
            <button
              onClick={() => setIsGalleryOpen(true)}
              className="w-full text-right text-xs text-gray-400 underline mt-2 hover:text-[#53B552]"
            >
              View all images →
            </button>
          </div>

          <hr className="border-gray-100 border-dashed" />

          {/* REVIEWS SECTION */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3
                className={`${jost.className} font-bold text-gray-900 text-lg`}
              >
                Feedbacks
              </h3>
              <button
                onClick={() => setIsReviewModalOpen(true)}
                className="flex items-center gap-1 text-[#53B552] text-sm font-bold bg-[#E9F5EB] px-3 py-1.5 rounded-full hover:bg-green-100 transition-colors"
              >
                <Plus size={16} /> Leave feedback
              </button>
            </div>

            <div className="space-y-4">
              {reviews.length > 0 ? (
                reviews.map((rev, idx) => (
                  <ReviewItem
                    key={idx}
                    review={rev}
                    isMe={currentUser && rev.user_id === currentUser.id}
                  />
                ))
              ) : (
                <div className="text-center py-8 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                  <p className="text-gray-400 text-sm">
                    No reviews yet. Be the first!
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* MODALS */}

        {/* 1. Add Review Modal */}
        {isReviewModalOpen && (
          <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white w-full max-w-md rounded-3xl p-6 shadow-2xl animate-in slide-in-from-bottom-10 duration-300">
              <div className="flex justify-between items-center mb-6">
                <h3
                  className={`${jost.className} font-bold text-xl text-gray-900`}
                >
                  Write a Review
                </h3>
                <button
                  onClick={() => setIsReviewModalOpen(false)}
                  className="bg-gray-100 p-2 rounded-full text-gray-500 hover:bg-gray-200"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex flex-col items-center mb-6">
                <p className="text-gray-500 text-sm mb-2">
                  How was your experience?
                </p>
                <RatingStars
                  rating={newRating}
                  setRating={setNewRating}
                  interactive
                  size={32}
                />
              </div>

              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Share your thoughts about this place..."
                className="w-full h-32 bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm outline-none focus:border-[#53B552] resize-none mb-4"
              />

              {reviewImages.length > 0 && (
                <div className="flex gap-2 mb-4 overflow-x-auto">
                  {reviewImages.map((file, idx) => (
                    <div key={idx} className="relative w-16 h-16 shrink-0">
                      <img
                        src={URL.createObjectURL(file)}
                        className="w-full h-full object-cover rounded-lg"
                      />
                      <button
                        onClick={() => removeImage(idx)}
                        className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-0.5"
                      >
                        <X size={10} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-3">
                <label className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-xl cursor-pointer hover:bg-gray-200 text-gray-500">
                  <Camera size={20} />
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    className="hidden"
                    onChange={handleImageUpload}
                  />
                </label>

                <button
                  onClick={submitReview}
                  disabled={!newComment.trim() || isSubmittingReview}
                  className="flex-1 bg-[#53B552] text-white font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isSubmittingReview ? "Posting..." : "Post Review"}{" "}
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 2. Gallery Modal */}
        {isGalleryOpen && place && place.photos && (
          <div className="fixed inset-0 z-60 bg-black bg-opacity-95 flex flex-col animate-in fade-in duration-300">
            <div className="flex justify-between items-center p-4 text-white">
              <h3 className={`${jost.className} font-bold text-lg`}>
                All Images ({place.photos.length})
              </h3>
              <button
                onClick={() => setIsGalleryOpen(false)}
                className="bg-white/10 p-2 rounded-full hover:bg-white/20"
              >
                <X size={24} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 grid grid-cols-2 gap-2 pb-20">
              {place.photos.map((photo, index) => (
                <img
                  key={index}
                  src={photo.photo_url}
                  className="w-full h-auto object-cover rounded-lg"
                  loading="lazy"
                  alt={`Gallery ${index}`}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
