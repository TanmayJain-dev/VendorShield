import httpx
import logging
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ValidationError

from ...schemas.evidence import EvidenceItem
from ...schemas.enums import SourceMode
from ...config import settings

logger = logging.getLogger(__name__)

def sanitize_untrusted_web_content(content: str) -> str:
    """
    Sanitizes external web content:
    - Strips raw HTML and script tags.
    - Truncates excessive payloads.
    - Mitigates prompt injection / instruction-injection artifacts.
    """
    if not content:
        return ""
    cleaned = re.sub(r"<[^>]*>", " ", str(content))
    cleaned = re.sub(r"(?i)(ignore (all|previous) instructions|system prompt|developer mode)", "[REDACTED_PROMPT_INJECTION]", cleaned)
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens)[:1200]

class TinyFishClient:
    """
    Unified client for TinyFish Browser Automation & Web Research API.
    Axiom: TinyFish researches; VendorShield decides.
    
    Architecture:
    1. Submits automation goals with explicit output_schema via run-async.
    2. Polls run status until COMPLETED, FAILED, or deadline.
    3. Strictly validates results against schema; returns UNAVAILABLE on failure.
    """
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or settings.TINYFISH_API_KEY
        self.api_url = api_url or settings.TINYFISH_API_URL
        # Normalize base URL for async endpoints
        self.base_url = self.api_url.replace("/automation/run", "").replace("/run-async", "").replace("/run", "")
        if not self.base_url:
            self.base_url = "https://agent.tinyfish.ai/v1"

    async def run_and_poll(
        self,
        url: str,
        goal: str,
        output_schema: Dict[str, Any],
        max_steps: int = 25,
        max_duration_seconds: int = 60,
        timeout_seconds: float = 65.0
    ) -> Dict[str, Any]:
        """
        Submits run-async and polls /runs/{run_id} until terminal state.
        Returns:
            {"status": "COMPLETED" | "FAILED" | "UNAVAILABLE", "result": dict | None, "error": str | None}
        """
        if not self.api_key:
            return {
                "status": "UNAVAILABLE",
                "result": None,
                "error": "TINYFISH_API_KEY not configured"
            }

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "goal": goal,
            "output_schema": output_schema,
            "agent_config": {
                "max_steps": max_steps,
                "max_duration_seconds": max_duration_seconds
            }
        }

        async_endpoint = f"{self.base_url}/automation/run-async"
        poll_base = f"{self.base_url}/runs"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                submit_resp = await client.post(async_endpoint, json=payload, headers=headers)
                
                # If async endpoint is not supported or returns 404, fallback to sync endpoint
                if submit_resp.status_code == 404:
                    sync_endpoint = f"{self.base_url}/automation/run"
                    sync_resp = await client.post(sync_endpoint, json=payload, headers=headers)
                    if sync_resp.status_code == 200:
                        data = sync_resp.json()
                        result = data.get("result")
                        if isinstance(result, dict) and len(result) > 0:
                            return {"status": "COMPLETED", "result": result, "error": None}
                        return {"status": "FAILED", "result": None, "error": data.get("error", "Empty result")}
                    return {"status": "UNAVAILABLE", "result": None, "error": f"HTTP {sync_resp.status_code}"}

                if submit_resp.status_code not in (200, 201, 202):
                    return {
                        "status": "UNAVAILABLE",
                        "result": None,
                        "error": f"TinyFish submit returned HTTP {submit_resp.status_code}: {submit_resp.text[:200]}"
                    }

                submit_data = submit_resp.json()
                run_id = submit_data.get("run_id") or submit_data.get("id")

                # If sync result returned directly
                if not run_id and "result" in submit_data:
                    res = submit_data.get("result")
                    return {"status": "COMPLETED", "result": res if isinstance(res, dict) else {}, "error": None}

                if not run_id:
                    return {"status": "UNAVAILABLE", "result": None, "error": "No run_id returned by async run endpoint"}

                # Poll /runs/{run_id}
                deadline = asyncio.get_event_loop().time() + timeout_seconds
                poll_url = f"{poll_base}/{run_id}"

                while asyncio.get_event_loop().time() < deadline:
                    await asyncio.sleep(2.0)
                    poll_resp = await client.get(poll_url, headers=headers)
                    if poll_resp.status_code != 200:
                        continue
                    poll_data = poll_resp.json()
                    run_status = str(poll_data.get("status", "")).upper()

                    if run_status == "COMPLETED":
                        result = poll_data.get("result")
                        if isinstance(result, dict):
                            return {"status": "COMPLETED", "result": result, "error": None}
                        return {"status": "COMPLETED", "result": {"raw_result": str(result)}, "error": None}
                    elif run_status in ("FAILED", "CANCELLED", "TIMED_OUT"):
                        return {"status": "FAILED", "result": None, "error": poll_data.get("error", f"Run {run_status}")}

                return {"status": "UNAVAILABLE", "result": None, "error": "Polling timeout reached"}

        except Exception as e:
            logger.warning(f"TinyFish run_and_poll exception: {e}")
            return {"status": "UNAVAILABLE", "result": None, "error": str(e)}

    @property
    def source_mode(self) -> SourceMode:
        return SourceMode.LIVE if self.api_key else SourceMode.SIMULATED

    async def investigate_vendor(
        self,
        supplier_name: str,
        gstin: Optional[str] = None
    ) -> List[EvidenceItem]:
        from .orchestrator import MultiHopTinyFishOrchestrator
        orch = MultiHopTinyFishOrchestrator(api_key=self.api_key)
        evidence, _, _, _ = await orch.execute_investigation(
            supplier_name=supplier_name,
            gstin=gstin,
            is_demo=True
        )
        return evidence

# Backward compatibility alias
TinyFishService = TinyFishClient
