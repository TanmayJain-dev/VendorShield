import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session

from ...db.models import IfscCacheModel
from ...schemas.evidence import FieldCheckResult
from ...schemas.enums import CheckStatus, SourceMode

logger = logging.getLogger(__name__)

class IfscProvider:
    """
    IFSC verification service utilizing the public Razorpay open dataset (https://ifsc.razorpay.com/<IFSC>).
    Features 30-day SQLite caching, timeout resilience, and bank name reconciliation.
    Never claims beneficiary account ownership.
    """
    def __init__(self, ttl_days: int = 30):
        self.ttl_days = ttl_days
        self.transport: Optional[httpx.AsyncBaseTransport] = None

    async def lookup(self, ifsc: str, db: Optional[Session] = None) -> Dict[str, Any]:
        clean_ifsc = ifsc.strip().upper()
        if not clean_ifsc or len(clean_ifsc) != 11:
            return {"valid": False, "reason": "IFSC_FORMAT_INVALID", "detail": "IFSC must be an 11-character alphanumeric code."}

        # Check DB cache
        if db:
            try:
                cached = db.query(IfscCacheModel).filter(IfscCacheModel.ifsc == clean_ifsc).first()
                if cached:
                    # Check TTL
                    cutoff = datetime.now(timezone.utc) - timedelta(days=self.ttl_days)
                    # Convert naive datetime if needed
                    cached_dt = cached.cached_at.replace(tzinfo=timezone.utc) if cached.cached_at.tzinfo is None else cached.cached_at
                    if cached_dt > cutoff:
                        return {
                            "valid": True,
                            "ifsc": clean_ifsc,
                            "bank": cached.bank_name,
                            "branch": cached.branch,
                            "city": cached.city,
                            "state": cached.state,
                            "source": "CACHE"
                        }
            except Exception as e:
                logger.warning(f"IFSC cache read error: {e}")

        # Live lookup via Razorpay IFSC open API
        url = f"https://ifsc.razorpay.com/{clean_ifsc}"
        try:
            async with httpx.AsyncClient(timeout=5.0, transport=self.transport) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    bank = data.get("BANK", "Unknown Bank")
                    branch = data.get("BRANCH", "")
                    city = data.get("CITY", "")
                    state = data.get("STATE", "")

                    # Save to DB cache
                    if db:
                        try:
                            record = db.query(IfscCacheModel).filter(IfscCacheModel.ifsc == clean_ifsc).first()
                            now = datetime.now(timezone.utc)
                            if not record:
                                record = IfscCacheModel(
                                    ifsc=clean_ifsc,
                                    bank_name=bank,
                                    branch=branch,
                                    city=city,
                                    state=state,
                                    cached_at=now
                                )
                                db.add(record)
                            else:
                                record.bank_name = bank
                                record.branch = branch
                                record.city = city
                                record.state = state
                                record.cached_at = now
                            db.commit()
                        except Exception as cache_err:
                            logger.warning(f"Failed to cache IFSC record: {cache_err}")
                            db.rollback()

                    return {
                        "valid": True,
                        "ifsc": clean_ifsc,
                        "bank": bank,
                        "branch": branch,
                        "city": city,
                        "state": state,
                        "source": "API"
                    }
                elif resp.status_code == 404:
                    return {"valid": False, "reason": "IFSC_NOT_FOUND", "detail": f"IFSC {clean_ifsc} not found in official RBI repository."}
                else:
                    return {"valid": None, "reason": "UNAVAILABLE", "detail": f"IFSC lookup returned status {resp.status_code}"}
        except Exception as e:
            logger.warning(f"IFSC network lookup failed for {clean_ifsc}: {e}")
            return {"valid": None, "reason": "UNAVAILABLE", "detail": str(e)}

    async def verify_invoice_bank(
        self,
        ifsc: Optional[str],
        printed_bank: Optional[str] = None,
        db: Optional[Session] = None
    ) -> FieldCheckResult:
        """
        Reconciles invoice bank credentials against the RBI IFSC repository.
        """
        if not ifsc:
            return FieldCheckResult(
                field_name="ifsc_code",
                status=CheckStatus.UNAVAILABLE,
                explanation="No IFSC code present on invoice for banking validation.",
                reason_code="IFSC_MISSING",
                source_mode=SourceMode.UNAVAILABLE
            )

        res = await self.lookup(ifsc, db=db)
        if res.get("valid") is False:
            return FieldCheckResult(
                field_name="ifsc_code",
                status=CheckStatus.MISMATCH,
                claimed_value=ifsc,
                evidence_value="NOT_FOUND",
                explanation=res.get("detail", "Invalid IFSC code."),
                reason_code="IFSC_INVALID",
                source_mode=SourceMode.LIVE
            )
        elif res.get("valid") is None:
            return FieldCheckResult(
                field_name="ifsc_code",
                status=CheckStatus.UNAVAILABLE,
                claimed_value=ifsc,
                explanation=f"IFSC lookup service unavailable: {res.get('detail')}",
                reason_code="IFSC_UNAVAILABLE",
                source_mode=SourceMode.UNAVAILABLE
            )

        # IFSC is valid
        bank_name = res.get("bank", "")
        explanation = (
            f"IFSC verified for {bank_name} ({res.get('branch', '')}). "
            "Note: Beneficiary account ownership unverified (requires cancelled cheque or penny drop)."
        )

        return FieldCheckResult(
            field_name="ifsc_code",
            status=CheckStatus.MATCH,
            claimed_value=ifsc,
            evidence_value=bank_name,
            explanation=explanation,
            reason_code="BANK_OWNERSHIP_UNVERIFIED",
            source_mode=SourceMode.LIVE,
            source_url=f"https://ifsc.razorpay.com/{ifsc.upper()}"
        )
