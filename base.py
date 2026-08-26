"""Base content generator abstract class."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.property import PropertyInput
from ..models.content import GeneratedContent


class BaseContentGenerator(ABC):
    """
    Abstract base class for content generators.
    
    Design Decision:
    - Using Strategy pattern allows swapping LLM providers (OpenAI, Anthropic, local)
    - Consistent interface regardless of underlying model
    - Easy to add new providers or test with mock generators
    """
    
    @abstractmethod
    async def generate(
        self, 
        property_data: PropertyInput,
        retry_count: int = 3,
    ) -> GeneratedContent:
        """
        Generate content for a property listing.
        
        Args:
            property_data: Validated property input data
            retry_count: Number of retries on failure
            
        Returns:
            GeneratedContent object with all sections
            
        Raises:
            ContentGenerationError: If generation fails after retries
        """
        pass
    
    @abstractmethod
    async def generate_batch(
        self,
        properties: list[PropertyInput],
        concurrency: int = 5,
    ) -> list[GeneratedContent]:
        """
        Generate content for multiple properties concurrently.
        
        Args:
            properties: List of property input data
            concurrency: Max concurrent generation tasks
            
        Returns:
            List of GeneratedContent objects
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, property_data: PropertyInput) -> float:
        """
        Estimate the cost of generating content for a property.
        
        Args:
            property_data: Property input data
            
        Returns:
            Estimated cost in USD
        """
        pass


class ContentGenerationError(Exception):
    """Exception raised when content generation fails."""
    
    def __init__(
        self, 
        message: str, 
        property_data: Optional[PropertyInput] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.property_data = property_data
        self.original_error = original_error


class ValidationError(Exception):
    """Exception raised when generated content fails validation."""
    
    def __init__(self, message: str, errors: list[str]):
        super().__init__(message)
        self.errors = errors

