import abc
from typing import Optional, Dict, Any
from ...schemas.evidence import EvidenceItem

class GstinProvider(abc.ABC):
    """Abstract interface for GST taxpayer registry lookups."""
    
    @abc.abstractmethod
    async def lookup(self, gstin: str, case_context: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        """Looks up a GSTIN and returns a structured EvidenceItem."""
        pass
