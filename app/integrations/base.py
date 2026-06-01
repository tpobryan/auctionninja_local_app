from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class PlatformIntegration(ABC):
    """Abstract base class for marketplace platform integrations (eBay, Etsy, etc.)."""

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Unique slug identifying the platform (e.g. 'ebay', 'etsy')."""
        pass


class AIService(ABC):
    """
    Abstract base class for an AI service that can generate item descriptions from images.
    """

    @abstractmethod
    def generate_options(
        self,
        image_paths: List[Path | str],
        seller_notes: str = "",
        strategy: str = "auction",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generates item description options from a list of images.

        :param image_paths: A list of paths to the images.
        :param seller_notes: Optional notes from the seller.
        :param strategy: The strategy to use for generation (e.g., 'auction', 'retail').
        :return: A dictionary containing a list of generated options.
        """
        pass

    @property
    def name(self) -> str:
        """
        Returns the name of the AI service (e.g., 'OpenAI', 'Claude', 'Gemini').
        """
        return self.__class__.__name__.replace("Client", "")