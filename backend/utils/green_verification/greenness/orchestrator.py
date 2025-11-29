"""
Self-contained orchestrator for calculating green coverage scores from images.
Combines TreeSegmenter (vegetation segmentation) and MiDaS (depth estimation).
"""

import os
import numpy as np
import torch
from typing import List, Dict, Any

from segmentation import TreeSegmenter
from model_loader import default_models, load_model
import utils
from run import process


class GreenCoverageOrchestrator:
    """Orchestrator for calculating green coverage scores from image URLs."""
    
    def __init__(
        self, 
        segmentation_model="best.pt", 
        depth_model_type="midas_v21_small_256",
        depth_model_path=None,
        green_threshold=0.3,
        optimize=False,
        height=None,
        square=False
    ):
        
        
        """
        Initialize the orchestrator with segmentation and depth models.
        
        Args:
            segmentation_model: Path to YOLO segmentation model
            depth_model_type: Type of MiDaS depth model
            depth_model_path: Optional custom path to depth model
            green_threshold: Threshold for green verification (0-1)
            optimize: Optimize depth model for CUDA
            height: Optional height for depth model
            square: Use square input for depth model
        """
        self.green_threshold = green_threshold
        
        # Initialize TreeSegmenter
        self.tree_segmenter = TreeSegmenter(segmentation_model)
        
        # Initialize MiDaS depth model with robust path handling
        if depth_model_path is None:
            depth_model_path = self._find_model_path(depth_model_type)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {self.device}")
        
        self.depth_model, self.depth_transform, self.net_w, self.net_h = load_model(
            self.device, depth_model_path, depth_model_type, optimize, height, square
        )
        self.depth_model_type = depth_model_type
        self.optimize = optimize
        
        print("Green Coverage Orchestrator initialized successfully")
    
    def _find_model_path(self, model_type: str) -> str:
        """
        Find the model path with fallback options.
        
        Args:
            model_type: The type of model to find
            
        Returns:
            Valid path to the model file
            
        Raises:
            FileNotFoundError: If no valid model path is found
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try multiple possible locations
        possible_paths = [
            # Default path from model_loader
            default_models.get(model_type, ""),
            # Same directory as this file
            os.path.join(current_dir, f"{model_type}.pt"),
            # Common model names in current directory
            os.path.join(current_dir, "midas_v21_small_256.pt"),
            os.path.join(current_dir, "best.pt"),
            # Weights subdirectory relative to current directory
            os.path.join(current_dir, "weights", f"{model_type}.pt"),
            # Parent directory weights folder
            os.path.join(os.path.dirname(current_dir), "weights", f"{model_type}.pt"),
        ]
        
        # Check each possible path
        for path in possible_paths:
            if path and os.path.exists(path):
                print(f"Found depth model at: {path}")
                return path
        
        # If no model found, provide helpful error message
        print(f"Available files in {current_dir}:")
        try:
            for file in os.listdir(current_dir):
                if file.endswith('.pt'):
                    print(f"  - {file}")
        except:
            pass
        
        raise FileNotFoundError(
            f"Could not find depth model for type '{model_type}'. "
            f"Please ensure the model file exists in one of these locations:\n" +
            "\n".join(f"  - {path}" for path in possible_paths if path)
        )
    
    def process_single_image(self, url: str) -> Dict[str, Any]:
        """
        Process a single image URL to calculate green coverage score.
        
        Args:
            url: Image URL to process
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Step 1: Load original image
            original_image_rgb = utils.load_image_from_url(url)  # RGB float32 in [0,1]
            
            # Step 2: Get vegetation segmentation
            combined_mask, _ = self.tree_segmenter.process_image(url)
            
            # Extract individual masks from YOLO results for completeness
            # Re-run YOLO to get individual masks
            individual_masks = self._get_individual_masks(url)
            
            # Step 3: Get depth map using MiDaS
            depth_map = self._get_depth_map(original_image_rgb)
            
            # Step 4: Calculate metrics
            total_pixels = combined_mask.size
            green_pixels = np.sum(combined_mask > 0)
            green_proportion = green_pixels / total_pixels if total_pixels > 0 else 0.0
            
            # Calculate depth-weighted green score
            if green_pixels > 0:
                # Get depth values where vegetation is present
                # Convert combined_mask to boolean for indexing
                mask_bool = combined_mask > 0
                vegetation_depths = depth_map[mask_bool]
                depth_weighted = np.mean(vegetation_depths) if len(vegetation_depths) > 0 else 0.0
            else:
                depth_weighted = 0.0
            
            # Calculate final green score
            green_score = green_proportion * depth_weighted
            
            # Determine verification status
            verified = green_score >= self.green_threshold
            
            return {
                "url": url,
                "combined_mask": combined_mask,
                "individual_masks": individual_masks,
                "depth": depth_map,
                "green_proportion": float(green_proportion),
                "depth_weighted": float(depth_weighted),
                "green_score": float(green_score),
                "verified": bool(verified)
            }
            
        except Exception as e:
            print(f"Error processing image {url}: {str(e)}")
            # Return empty result on error
            return {
                "url": url,
                "combined_mask": np.array([]),
                "individual_masks": [],
                "depth": np.array([]),
                "green_proportion": 0.0,
                "depth_weighted": 0.0,
                "green_score": 0.0,
                "verified": False,
                "error": str(e)
            }
    
    def _get_combined_masks(self, url: str) -> np.ndarray:
        """Get combined vegetation mask from YOLO segmentation."""
        try:
            # 1. Use TreeSegmenter to get combined mask
            combined_mask, _ = self.tree_segmenter.process_image(url)

            return combined_mask

        except Exception as e:
            print(f"Error getting combined mask: {str(e)}")
            return np.array([], dtype=np.uint8)
    
    def _get_depth_map(self, image_rgb: np.ndarray) -> np.ndarray:
        """Get depth map from RGB image using MiDaS."""
        try:
            # Transform image for MiDaS
            image_input = self.depth_transform({"image": image_rgb})["image"]
            
            # Run depth estimation
            with torch.no_grad():
                prediction = process(
                    self.device, 
                    self.depth_model, 
                    self.depth_model_type, 
                    image_input, 
                    (self.net_w, self.net_h), 
                    image_rgb.shape[1::-1],  # (width, height)
                    self.optimize, 
                    False
                )
            
            return prediction.astype(np.float32)
            
        except Exception as e:
            print(f"Error getting depth map: {str(e)}")
            # Return empty depth map on error
            return np.zeros(image_rgb.shape[:2], dtype=np.float32)
    
    def process_image_list(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of image URLs to calculate green coverage scores.
        
        Args:
            image_urls: List of image URLs to process
            
        Returns:
            List of dictionaries containing analysis results for each image
        """
        print(f"Processing {len(image_urls)} images...")
        results = []
        
        for i, url in enumerate(image_urls):
            print(f"Processing image {i+1}/{len(image_urls)}: {url}")
            result = self.process_single_image(url)
            results.append(result)
        
        print("Processing complete!")
        return results
    
    def get_summary_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics from processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            Dictionary with summary statistics
        """
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            return {
                "total_images": len(results),
                "valid_images": 0,
                "verified_images": 0,
                "average_green_proportion": 0.0,
                "average_green_score": 0.0,
                "verification_rate": 0.0
            }
        
        green_proportions = [r["green_proportion"] for r in valid_results]
        green_scores = [r["green_score"] for r in valid_results]
        verified_count = sum(1 for r in valid_results if r["verified"])
        
        return {
            "total_images": len(results),
            "valid_images": len(valid_results),
            "verified_images": verified_count,
            "average_green_proportion": float(np.mean(green_proportions)),
            "average_green_score": float(np.mean(green_scores)),
            "verification_rate": float(verified_count / len(valid_results)) if valid_results else 0.0
        }


def main():
    """Example usage of the GreenCoverageOrchestrator."""
    # Example image URLs
    image_urls = [
        "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzMja-cKxl1dNoPaSKLzLLTvNrCsLblTsd3mVZgwZEdxO7gi5CSU0yp6MDc6hG8OiFTB9U_XRM-72uZSNj5leBO-ulnbiwIFP5MQP3SqeyYo7RD6ygj06WYZoFyrsHnXDo_zmruDw=w203-h270-k-no"
    ]
    
    # Initialize orchestrator with more robust model handling
    try:
        orchestrator = GreenCoverageOrchestrator(
            segmentation_model="best.pt",
            depth_model_type="midas_v21_small_256", 
            green_threshold=0.3,
            optimize=True
        )
        
        # Process images
        results = orchestrator.process_image_list(image_urls)
        
        # Print results
        for result in results:
            print(f"\nResults for {result['url']}:")
            print(f"  Green proportion: {result['green_proportion']:.3f}")
            print(f"  Depth weighted: {result['depth_weighted']:.3f}")
            print(f"  Green score: {result['green_score']:.3f}")
            print(f"  Verified: {result['verified']}")
            
            if "error" in result:
                print(f"  Error: {result['error']}")
        
        # Get summary statistics
        summary = orchestrator.get_summary_stats(results)
        print(f"\nSummary Statistics:")
        print(f"  Total images: {summary['total_images']}")
        print(f"  Valid images: {summary['valid_images']}")
        print(f"  Verified images: {summary['verified_images']}")
        print(f"  Average green proportion: {summary['average_green_proportion']:.3f}")
        print(f"  Average green score: {summary['average_green_score']:.3f}")
        print(f"  Verification rate: {summary['verification_rate']:.3f}")
        
    except FileNotFoundError as e:
        print(f"Model file error: {e}")
        print("\nTo fix this issue:")
        print("1. Download the MiDaS model weights from the official repository")
        print("2. Place the .pt files in the same directory as this script")
        print("3. Or create a 'weights/' subdirectory and place them there")
        print("\nAlternatively, you can use a simpler model like 'dpt_swin2_tiny_256' if available")


if __name__ == "__main__":
    main()