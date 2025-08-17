"""
Image preprocessing utilities for vocabulary OCR.
Provides various image enhancement techniques to improve OCR accuracy.
"""

import os
import io
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
from core.image_config import ImagePreprocessingConfig, DEFAULT_CONFIG

class ImagePreprocessor:
    """Handles image preprocessing pipeline for OCR optimization."""
    
    def __init__(self, config: ImagePreprocessingConfig = None):
        self.config = config or DEFAULT_CONFIG
        
        # Ensure debug directory exists if needed
        if self.config.save_intermediate_steps:
            os.makedirs(self.config.intermediate_dir, exist_ok=True)
        
        # Ensure processed image directory exists if needed
        if self.config.save_processed_image:
            os.makedirs(self.config.processed_image_dir, exist_ok=True)
    
    def preprocess_image(self, image_path: str) -> Tuple[Image.Image, str]:
        """
        Apply full preprocessing pipeline to an image.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Tuple of (processed_image, processing_summary)
        """
        if not self.config.enable_preprocessing:
            image = Image.open(image_path)
            return image, "Preprocessing disabled - using original image"
        
        print(f"🔧 Starting image preprocessing pipeline...")
        
        # Load original image
        image = Image.open(image_path)
        original_size = image.size
        processing_steps = []
        
        # Save original for debugging
        if self.config.save_intermediate_steps:
            debug_path = os.path.join(self.config.intermediate_dir, "01_original.png")
            image.save(debug_path)
            processing_steps.append(f"Saved original: {debug_path}")
        
        step = 2
        
        # Step 1: Resize if needed
        if self.config.enable_resize:
            image, resize_info = self._resize_image(image)
            processing_steps.append(resize_info)
            
            if self.config.save_intermediate_steps:
                debug_path = os.path.join(self.config.intermediate_dir, f"{step:02d}_resized.png")
                image.save(debug_path)
                step += 1
        
        # Step 2: Enhance contrast
        if self.config.enable_contrast:
            image, contrast_info = self._enhance_contrast(image)
            processing_steps.append(contrast_info)
            
            if self.config.save_intermediate_steps:
                debug_path = os.path.join(self.config.intermediate_dir, f"{step:02d}_contrast.png")
                image.save(debug_path)
                step += 1
        
        # Step 3: Noise reduction
        if self.config.enable_noise_reduction:
            image, noise_info = self._reduce_noise(image)
            processing_steps.append(noise_info)
            
            if self.config.save_intermediate_steps:
                debug_path = os.path.join(self.config.intermediate_dir, f"{step:02d}_denoised.png")
                image.save(debug_path)
                step += 1
        
        # Step 4: Sharpening
        if self.config.enable_sharpening:
            image, sharp_info = self._sharpen_image(image)
            processing_steps.append(sharp_info)
            
            if self.config.save_intermediate_steps:
                debug_path = os.path.join(self.config.intermediate_dir, f"{step:02d}_sharpened.png")
                image.save(debug_path)
                step += 1
        
        # Step 5: Compression (if enabled)
        if self.config.enable_compression:
            image, compress_info = self._compress_image(image)
            processing_steps.append(compress_info)
            
            if self.config.save_intermediate_steps:
                debug_path = os.path.join(self.config.intermediate_dir, f"{step:02d}_compressed.png")
                image.save(debug_path)
        
        summary = f"Processed {original_size} → {image.size}: " + " | ".join(processing_steps)
        print(f"✅ Preprocessing complete: {summary}")
        
        # Save final processed image if enabled
        if self.config.save_processed_image:
            try:
                # Generate output filename based on input filename
                input_basename = os.path.splitext(os.path.basename(image_path))[0]
                output_filename = f"{input_basename}_processed.{self.config.output_format.lower()}"
                output_path = os.path.join(self.config.processed_image_dir, output_filename)
                
                # Save the processed image
                if self.config.output_format.upper() == "JPEG":
                    # Convert to RGB if needed for JPEG
                    save_image = image
                    if image.mode in ("RGBA", "LA", "P"):
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        if image.mode == "P":
                            save_image = image.convert("RGBA")
                        background.paste(save_image, mask=save_image.split()[-1] if save_image.mode in ("RGBA", "LA") else None)
                        save_image = background
                    elif image.mode != "RGB":
                        save_image = image.convert("RGB")
                    
                    save_image.save(output_path, format="JPEG", quality=self.config.jpeg_quality, optimize=True)
                else:
                    image.save(output_path, format=self.config.output_format, optimize=True)
                
                print(f"💾 Saved processed image to: {output_path}")
                processing_steps.append(f"Saved to {output_path}")
                
            except Exception as e:
                print(f"⚠️ Warning: Could not save processed image: {e}")
        
        return image, summary
    
    def _resize_image(self, image: Image.Image) -> Tuple[Image.Image, str]:
        """Resize image if it exceeds maximum dimensions."""
        original_size = image.size
        max_w, max_h = self.config.max_width, self.config.max_height
        
        if original_size[0] <= max_w and original_size[1] <= max_h:
            return image, f"No resize needed ({original_size[0]}x{original_size[1]})"
        
        # Calculate new size maintaining aspect ratio
        ratio = min(max_w / original_size[0], max_h / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        
        # Get resampling filter
        resample_map = {
            "LANCZOS": Image.Resampling.LANCZOS,
            "BICUBIC": Image.Resampling.BICUBIC,
            "BILINEAR": Image.Resampling.BILINEAR,
            "NEAREST": Image.Resampling.NEAREST
        }
        resample = resample_map.get(self.config.resize_quality, Image.Resampling.LANCZOS)
        
        resized = image.resize(new_size, resample)
        return resized, f"Resized {original_size} → {new_size} ({self.config.resize_quality})"
    
    def _enhance_contrast(self, image: Image.Image) -> Tuple[Image.Image, str]:
        """Enhance image contrast for better text visibility."""
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(self.config.contrast_factor)
        return enhanced, f"Contrast enhanced (factor: {self.config.contrast_factor})"
    
    def _reduce_noise(self, image: Image.Image) -> Tuple[Image.Image, str]:
        """Apply noise reduction using Gaussian blur."""
        if self.config.noise_reduction_radius <= 0:
            return image, "Noise reduction skipped (radius: 0)"
        
        denoised = image.filter(ImageFilter.GaussianBlur(radius=self.config.noise_reduction_radius))
        return denoised, f"Noise reduced (radius: {self.config.noise_reduction_radius})"
    
    def _sharpen_image(self, image: Image.Image) -> Tuple[Image.Image, str]:
        """Apply sharpening filter to improve text clarity."""
        if self.config.sharpening_factor <= 1.0:
            return image, "Sharpening skipped (factor: 1.0)"
        
        # Create custom sharpening filter
        sharpening_filter = ImageFilter.UnsharpMask(
            radius=2.0,
            percent=int((self.config.sharpening_factor - 1.0) * 100),
            threshold=self.config.sharpening_threshold
        )
        
        sharpened = image.filter(sharpening_filter)
        return sharpened, f"Sharpened (factor: {self.config.sharpening_factor})"
    
    def _compress_image(self, image: Image.Image) -> Tuple[Image.Image, str]:
        """Apply compression to reduce memory usage."""
        if self.config.output_format.upper() == "JPEG":
            # Convert to JPEG with quality setting
            if image.mode in ("RGBA", "LA", "P"):
                # Convert transparent images to RGB with white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            
            # Save to bytes and reload to apply compression
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.config.jpeg_quality, optimize=True)
            # Don't reload - return bytes size info instead of reloading image
            compressed_size = len(buffer.getvalue())
            return image, f"JPEG compressed (quality: {self.config.jpeg_quality}, size: {compressed_size} bytes)"
        
        elif self.config.output_format.upper() == "PNG":
            # Apply PNG compression
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", compress_level=self.config.png_compress_level, optimize=True)
            compressed_size = len(buffer.getvalue())
            return image, f"PNG compressed (level: {self.config.png_compress_level}, size: {compressed_size} bytes)"
        
        return image, "No compression applied"

def preprocess_image_for_ocr(image_path: str, config: ImagePreprocessingConfig = None) -> Tuple[Image.Image, str]:
    """
    Convenience function to preprocess an image for OCR.
    
    Args:
        image_path: Path to the input image
        config: Preprocessing configuration (uses default if None)
        
    Returns:
        Tuple of (processed_image, processing_summary)
    """
    preprocessor = ImagePreprocessor(config)
    return preprocessor.preprocess_image(image_path)

def get_preprocessing_stats(original_path: str, processed_image: Image.Image, config: ImagePreprocessingConfig = None) -> dict:
    """Get statistics about the preprocessing results."""
    original_size = os.path.getsize(original_path)
    
    # Get processed image size estimate based on output format
    buffer = io.BytesIO()
    if config and config.output_format.upper() == "JPEG":
        # Convert to RGB if needed for JPEG
        save_image = processed_image
        if processed_image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", processed_image.size, (255, 255, 255))
            if processed_image.mode == "P":
                save_image = processed_image.convert("RGBA")
            background.paste(save_image, mask=save_image.split()[-1] if save_image.mode in ("RGBA", "LA") else None)
            save_image = background
        elif processed_image.mode != "RGB":
            save_image = processed_image.convert("RGB")
            
        save_image.save(buffer, format="JPEG", quality=config.jpeg_quality, optimize=True)
    else:
        processed_image.save(buffer, format="PNG", optimize=True)
    processed_size = len(buffer.getvalue())
    
    original_dims = Image.open(original_path).size
    processed_dims = processed_image.size
    
    return {
        "original_file_size": original_size,
        "processed_file_size": processed_size,
        "size_reduction_percent": ((original_size - processed_size) / original_size) * 100,
        "original_dimensions": original_dims,
        "processed_dimensions": processed_dims,
        "dimension_reduction_percent": ((original_dims[0] * original_dims[1] - processed_dims[0] * processed_dims[1]) / (original_dims[0] * original_dims[1])) * 100
    }
