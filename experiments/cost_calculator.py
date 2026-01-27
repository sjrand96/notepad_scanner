import math
from PIL import Image


class ImageAnalysisCostCalculator:
    """
    Calculates the cost (in tokens and dollars) for analyzing images with OpenAI's Vision API.
    
    Based on OpenAI's pricing structure:
    - Low detail: Fixed base cost per image
    - High detail: Base cost + cost per 512x512 tile
    - Images are scaled: max dimension 2048px, min dimension 768px
    - Image tokens are billed at the same rate as text input tokens for vision-capable models
    """
    
    # Model-specific token costs
    # Format: {model_name: {'base': base_tokens, 'tile': tokens_per_tile}}
    MODEL_COSTS = {
        'gpt-4.1': {'base': 85, 'tile': 170},
        'gpt-4o': {'base': 85, 'tile': 170},
        'gpt-4o-mini': {'base': 85, 'tile': 170},
        'gpt-4-turbo': {'base': 85, 'tile': 170},
        'gpt-4': {'base': 85, 'tile': 170},
        'gpt-5': {'base': 70, 'tile': 140},
        'gpt-5.1': {'base': 70, 'tile': 140},
        'gpt-5-mini': {'base': 70, 'tile': 140},
        'gpt-5-nano': {'base': 70, 'tile': 140},
        'gpt-5-pro': {'base': 70, 'tile': 140},
        'o1': {'base': 75, 'tile': 150},
        'o1-pro': {'base': 75, 'tile': 150},
        'o1-mini': {'base': 75, 'tile': 150},
        'o3': {'base': 75, 'tile': 150},
        'o3-pro': {'base': 75, 'tile': 150},
        'o3-mini': {'base': 75, 'tile': 150},
        'o3-deep-research': {'base': 75, 'tile': 150},
        'o4-mini': {'base': 75, 'tile': 150},
        'o4-mini-deep-research': {'base': 75, 'tile': 150},
        'computer-use-preview': {'base': 65, 'tile': 129},
        'gpt-image-1': {'base': 85, 'tile': 170},
        'gpt-image-1-mini': {'base': 85, 'tile': 170},
    }
    
    # Pricing per 1M tokens (input) for different tiers
    # Format: {tier: {model: price_per_1M_tokens}}
    PRICING_BATCH = {
        'gpt-5.1': 0.625,
        'gpt-5': 0.625,
        'gpt-5-mini': 0.125,
        'gpt-5-nano': 0.025,
        'gpt-5-pro': 7.50,
        'gpt-4.1': 1.00,
        'gpt-4.1-mini': 0.20,
        'gpt-4.1-nano': 0.05,
        'gpt-4o': 1.25,
        'gpt-4o-mini': 0.075,
        'o1': 7.50,
        'o1-pro': 75.00,
        'o3-pro': 10.00,
        'o3': 1.00,
        'o3-deep-research': 5.00,
        'o4-mini': 0.55,
        'o4-mini-deep-research': 1.00,
        'o3-mini': 0.55,
        'o1-mini': 0.55,
        'computer-use-preview': 1.50,
        'gpt-image-1': 10.00,
        'gpt-image-1-mini': 2.50,
    }
    
    PRICING_STANDARD = {
        'gpt-5.1': 1.25,
        'gpt-5': 1.25,
        'gpt-5-mini': 0.25,
        'gpt-5-nano': 0.05,
        'gpt-5-pro': 15.00,
        'gpt-4.1': 2.00,
        'gpt-4.1-mini': 0.40,
        'gpt-4.1-nano': 0.10,
        'gpt-4o': 2.50,
        'gpt-4o-mini': 0.15,
        'o1': 15.00,
        'o1-pro': 150.00,
        'o3-pro': 20.00,
        'o3': 2.00,
        'o3-deep-research': 10.00,
        'o4-mini': 1.10,
        'o4-mini-deep-research': 2.00,
        'o3-mini': 1.10,
        'o1-mini': 1.10,
        'computer-use-preview': 3.00,
        'gpt-image-1': 10.00,
        'gpt-image-1-mini': 2.50,
    }
    
    PRICING_PRIORITY = {
        'gpt-5.1': 2.50,
        'gpt-5': 2.50,
        'gpt-5-mini': 0.45,
        'gpt-4.1': 3.50,
        'gpt-4.1-mini': 0.70,
        'gpt-4.1-nano': 0.20,
        'gpt-4o': 4.25,
        'gpt-4o-mini': 0.25,
        'o3': 3.50,
        'o4-mini': 2.00,
    }
    
    PRICING_FLEX = {
        'gpt-5.1': 0.625,
        'gpt-5': 0.625,
        'gpt-5-mini': 0.125,
        'gpt-5-nano': 0.025,
        'o3': 1.00,
        'o4-mini': 0.55,
    }
    
    def __init__(self, model='gpt-4.1', tier='standard'):
        """
        Initialize the cost calculator.
        
        Args:
            model: The OpenAI model name (default: 'gpt-4.1')
            tier: Pricing tier - 'batch', 'standard', 'priority', or 'flex' (default: 'standard')
        """
        if model not in self.MODEL_COSTS:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {list(self.MODEL_COSTS.keys())}"
            )
        
        tier = tier.lower()
        pricing_map = {
            'batch': self.PRICING_BATCH,
            'standard': self.PRICING_STANDARD,
            'priority': self.PRICING_PRIORITY,
            'flex': self.PRICING_FLEX,
        }
        
        if tier not in pricing_map:
            raise ValueError(
                f"Unsupported tier: {tier}. "
                f"Supported tiers: {list(pricing_map.keys())}"
            )
        
        pricing = pricing_map[tier]
        if model not in pricing:
            raise ValueError(
                f"Model '{model}' not available in '{tier}' tier. "
                f"Available models: {list(pricing.keys())}"
            )
        
        self.model = model
        self.tier = tier
        self.base_tokens = self.MODEL_COSTS[model]['base']
        self.tile_tokens = self.MODEL_COSTS[model]['tile']
        self.price_per_1M_tokens = pricing[model]
    
    def _scale_image_dimensions(self, width, height):
        """
        Scale image dimensions according to OpenAI's rules:
        - Scale to fit within 2048x2048 square (maintaining aspect ratio)
        - Scale so shortest side is at least 768px
        
        Args:
            width: Original image width
            height: Original image height
            
        Returns:
            Tuple of (scaled_width, scaled_height)
        """
        # Step 1: Scale to fit within 2048x2048 square
        max_dim = max(width, height)
        if max_dim > 2048:
            scale_factor = 2048 / max_dim
            width = int(width * scale_factor)
            height = int(height * scale_factor)
        
        # Step 2: Scale so shortest side is at least 768px
        min_dim = min(width, height)
        if min_dim < 768:
            scale_factor = 768 / min_dim
            width = int(width * scale_factor)
            height = int(height * scale_factor)
        
        return width, height
    
    def _calculate_tiles(self, width, height):
        """
        Calculate the number of 512x512 tiles needed to cover the image.
        
        Args:
            width: Image width (after scaling)
            height: Image height (after scaling)
            
        Returns:
            Number of tiles needed
        """
        tiles_width = math.ceil(width / 512)
        tiles_height = math.ceil(height / 512)
        return tiles_width * tiles_height
    
    def calculate_tokens(self, image_path=None, width=None, height=None, detail='high'):
        """
        Calculate the total token cost for analyzing an image.
        
        Args:
            image_path: Path to the image file (optional if width/height provided)
            width: Image width in pixels (optional if image_path provided)
            height: Image height in pixels (optional if image_path provided)
            detail: Detail level - 'low' or 'high' (default: 'high')
            
        Returns:
            Total token cost as integer
        """
        if detail not in ['low', 'high']:
            raise ValueError("Detail must be 'low' or 'high'")
        
        # Low detail: just return base cost
        if detail == 'low':
            return self.base_tokens
        
        # High detail: need image dimensions
        if image_path:
            with Image.open(image_path) as img:
                width, height = img.size
        elif width is None or height is None:
            raise ValueError("Must provide either image_path or both width and height")
        
        # Scale dimensions according to OpenAI's rules
        scaled_width, scaled_height = self._scale_image_dimensions(width, height)
        
        # Calculate number of tiles
        num_tiles = self._calculate_tiles(scaled_width, scaled_height)
        
        # Calculate total tokens: base + (tiles * tokens_per_tile)
        total_tokens = self.base_tokens + (num_tiles * self.tile_tokens)
        
        return total_tokens
    
    def calculate_cost(self, image_path=None, width=None, height=None, detail='high'):
        """
        Calculate the cost for analyzing an image.
        This is an alias for calculate_tokens() for consistency.
        
        Args:
            image_path: Path to the image file (optional if width/height provided)
            width: Image width in pixels (optional if image_path provided)
            height: Image height in pixels (optional if image_path provided)
            detail: Detail level - 'low' or 'high' (default: 'high')
            
        Returns:
            Total token cost as integer
        """
        return self.calculate_tokens(image_path, width, height, detail)
    
    def calculate_cost_dollars(self, image_path=None, width=None, height=None, detail='high'):
        """
        Calculate the cost in dollars for analyzing an image.
        
        Args:
            image_path: Path to the image file (optional if width/height provided)
            width: Image width in pixels (optional if image_path provided)
            height: Image height in pixels (optional if image_path provided)
            detail: Detail level - 'low' or 'high' (default: 'high')
            
        Returns:
            Cost in dollars as float
        """
        tokens = self.calculate_tokens(image_path, width, height, detail)
        # Convert tokens to cost: (tokens / 1,000,000) * price_per_1M_tokens
        cost = (tokens / 1_000_000) * self.price_per_1M_tokens
        return cost
    
    def calculate_cost_both(self, image_path=None, width=None, height=None, detail='high'):
        """
        Calculate both token cost and dollar cost for analyzing an image.
        
        Args:
            image_path: Path to the image file (optional if width/height provided)
            width: Image width in pixels (optional if image_path provided)
            height: Image height in pixels (optional if image_path provided)
            detail: Detail level - 'low' or 'high' (default: 'high')
            
        Returns:
            Dictionary with 'tokens' and 'dollars' keys
        """
        tokens = self.calculate_tokens(image_path, width, height, detail)
        dollars = (tokens / 1_000_000) * self.price_per_1M_tokens
        return {
            'tokens': tokens,
            'dollars': dollars,
            'model': self.model,
            'tier': self.tier,
        }
