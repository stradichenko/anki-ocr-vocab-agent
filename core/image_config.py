"""
Image preprocessing configuration settings.
Allows easy customization of image processing parameters.
"""

from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class ImagePreprocessingConfig:
    """Configuration for image preprocessing pipeline."""
    
    # Enable/disable preprocessing steps
    enable_preprocessing: bool = True
    enable_resize: bool = True
    enable_compression: bool = True
    enable_contrast: bool = True
    enable_noise_reduction: bool = True
    enable_sharpening: bool = True
    
    # Resize settings
    max_width: int = 2048
    max_height: int = 2048
    resize_quality: str = "LANCZOS"  # LANCZOS, BICUBIC, BILINEAR, NEAREST
    
    # Compression settings
    jpeg_quality: int = 85
    png_compress_level: int = 6
    
    # Contrast enhancement
    contrast_factor: float = 1.2  # 1.0 = no change, >1.0 = more contrast
    
    # Noise reduction (Gaussian blur)
    noise_reduction_radius: float = 0.5  # 0 = no blur, higher = more blur
    
    # Sharpening
    sharpening_factor: float = 1.5  # 1.0 = no sharpening, >1.0 = more sharp
    sharpening_threshold: int = 3
    
    # Output format
    output_format: str = "PNG"  # PNG, JPEG
    
    # Debug settings
    save_intermediate_steps: bool = False
    intermediate_dir: str = "output/preprocessing_debug"
    save_processed_image: bool = False  # New option to save final processed image
    processed_image_dir: str = "output/processed_images"  # Directory for processed images

# Default configuration instance
DEFAULT_CONFIG = ImagePreprocessingConfig()

# Quick presets for different use cases
FAST_CONFIG = ImagePreprocessingConfig(
    enable_preprocessing=True,
    enable_resize=True,
    enable_compression=True,
    enable_contrast=False,
    enable_noise_reduction=False,
    enable_sharpening=False,
    max_width=1536,
    max_height=1536,
    jpeg_quality=75,
    output_format="JPEG"  # Use JPEG for smaller files
)

QUALITY_CONFIG = ImagePreprocessingConfig(
    enable_preprocessing=True,
    enable_resize=True,
    enable_compression=True,  # Enable compression to control file size
    enable_contrast=True,
    enable_noise_reduction=True,
    enable_sharpening=True,
    max_width=2048,
    max_height=2048,
    contrast_factor=1.3,
    noise_reduction_radius=0.3,
    sharpening_factor=2.0,
    output_format="JPEG",  # Use JPEG instead of PNG for smaller files
    jpeg_quality=90  # High quality JPEG
)

# Add new optimized config for your case
OPTIMIZED_CONFIG = ImagePreprocessingConfig(
    enable_preprocessing=True,
    enable_resize=True,
    enable_compression=True,
    enable_contrast=True,
    enable_noise_reduction=True,
    enable_sharpening=True,
    max_width=1024,  # Force resize to smaller dimensions
    max_height=768,   # Force resize to smaller dimensions  
    contrast_factor=1.2,  # Moderate contrast
    noise_reduction_radius=0.2,  # Light noise reduction
    sharpening_factor=1.3,  # Moderate sharpening
    output_format="JPEG",
    jpeg_quality=85,
    save_intermediate_steps=False,
    save_processed_image=True  # Enable saving processed images by default
)

# Add a specific config that forces smaller images
OCR_OPTIMIZED_CONFIG = ImagePreprocessingConfig(
    enable_preprocessing=True,
    enable_resize=True,
    enable_compression=True,
    enable_contrast=True,
    enable_noise_reduction=True,
    enable_sharpening=True,
    max_width=800,   # Much smaller for OCR
    max_height=600,  # Much smaller for OCR
    contrast_factor=1.4,  # Higher contrast for text
    noise_reduction_radius=0.1,  # Minimal blur to preserve text
    sharpening_factor=1.5,  # More sharpening for text clarity
    output_format="JPEG",
    jpeg_quality=80,
    save_intermediate_steps=False,
    save_processed_image=True  # Enable saving processed images by default
)

MINIMAL_CONFIG = ImagePreprocessingConfig(
    enable_preprocessing=False
)
