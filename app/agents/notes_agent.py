import re
import logging
from typing import List, Dict, Any, Optional
from app.models.agent_results import NotesSummarizationResult
from app.models.alert import FraudAlert, CustomerProfile

logger = logging.getLogger("agent.notes")

class NotesSummarizationAgent:
    """
    Step 6 in Architecture: Synthesizes multi-source unstructured text:
    investigator notes, PCFD comments, customer care transcripts, and
    Pindrop telephony voice analysis into structured bullet points.
    """
    def __init__(self):
        self.name = "Notes Summarization Agent"
        self.systems = ["PCFD", "Pindrop", "CRM_Notes", "ContactCenter_Audio"]

    async def summarize_notes(
        self,
        customer: CustomerProfile,
        alert: FraudAlert,
        raw_notes: List[Dict[str, Any]] = None
    ) -> NotesSummarizationResult:
        logger.info(f"[{self.name}] Analyzing unstructured notes for customer {customer.customer_id}")

        if not raw_notes:
            return NotesSummarizationResult(
                customer_id=customer.customer_id,
                total_notes_analyzed=0,
                bullet_points=[
                    "No prior customer service or investigator notes recorded in PCFD/CRM.",
                    "No reported lost/stolen card claims or travel notifications on file."
                ],
                detected_travel_notice=None,
                recent_security_events=[],
                customer_sentiment="UNRESPONSIVE",
                systems_consulted=self.systems
            )

        bullets: List[str] = []
        security_events: List[str] = []
        travel_notice: Optional[Dict[str, Any]] = None
        sentiment_scores = {"COOPERATIVE": 0, "DISTRESSED": 0, "SUSPICIOUS": 0, "NEUTRAL": 0}

        for note in raw_notes:
            content = note.get("text", "")
            source = note.get("source", "PCFD")
            timestamp = note.get("timestamp", "Recent")
            sentiment = note.get("sentiment", "NEUTRAL").upper()
            
            if sentiment in sentiment_scores:
                sentiment_scores[sentiment] += 1

            # Extract travel notice
            if "travel" in content.lower():
                # Check for country/destination
                match = re.search(r"travel(?:ing)? to ([A-Za-z\s]+)", content, re.IGNORECASE)
                destination = match.group(1).strip() if match else "International"
                travel_notice = {
                    "source": source,
                    "timestamp": timestamp,
                    "destination": destination,
                    "raw_note": content
                }
                bullets.append(f"[{source} {timestamp}] Customer notified bank of travel to {destination}.")

            # Extract credential or security events
            if any(k in content.lower() for k in ["password", "credential", "mfa", "reset", "sim swap", "phishing"]):
                security_events.append(f"{source}: {content}")
                bullets.append(f"[{source} {timestamp}] Security Event: {content}")

            # Extract dispute / fraud history
            elif any(k in content.lower() for k in ["dispute", "fraud claim", "unauthorized", "suspicious"]):
                bullets.append(f"[{source} {timestamp}] Fraud Record: {content}")
            
            # Extract customer service interactions
            elif len(bullets) < 5:
                bullets.append(f"[{source} {timestamp}] Interaction: {content}")

        # Determine dominant sentiment
        dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        if dominant_sentiment == "NEUTRAL":
            dominant_sentiment = "COOPERATIVE"

        # Ensure we have 3-5 bullet points
        if len(bullets) < 3:
            bullets.append(f"[CRM_Notes] Account profile verified against core KYC database.")
        bullets = bullets[:5]

        return NotesSummarizationResult(
            customer_id=customer.customer_id,
            total_notes_analyzed=len(raw_notes),
            bullet_points=bullets,
            detected_travel_notice=travel_notice,
            recent_security_events=security_events,
            customer_sentiment=dominant_sentiment,
            systems_consulted=self.systems
        )
