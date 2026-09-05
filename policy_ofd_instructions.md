# Online Fraud Detection (OFD) Policy Instructions

## SOP-SEC-802: Account Takeover Emergency Containment
- **Trigger Conditions:** Foreign IP session + new unrecognized device + credential/password reset within 48 hours.
- **Mandatory Action:** Immediately freeze account, revoke active mobile/web sessions, and restrict debit cards.
- **Urgency:** Immediate (< 15 minutes).

## SOP-OFD-403: Card Not Present Velocity Spree
- **Trigger Conditions:** >= 3 online purchases within 10 minutes at high-risk MCCs (gift cards, electronics, digital assets) on low-trust proxy.
- **Mandatory Action:** Place temporary card block; trigger customer notification SMS.
- **Urgency:** High (< 1 hour).

## SOP-EXEMP-105: Verified Travel & Strong Authentication Exemption
- **Trigger Conditions:** International transaction where customer travel notice is on file matching destination AND hardware biometric auth (FaceID/Fingerprint) confidence >= 95%.
- **Mandatory Action:** Dismiss alert as verified authorized customer activity.
- **Urgency:** Routine.

## SOP-MULE-901: Rapid Dispersion / Layering
- **Trigger Conditions:** Account tenure < 3 months receiving government/corporate disbursement followed by immediate P2P/UPI/crypto off-ramp attempt.
- **Mandatory Action:** Block outbound payments, freeze VPA handles, and escalate to AML/Financial Crimes Unit.
- **Urgency:** Immediate (< 30 minutes).

## SOP-RBI-UPI-109: Remote Access & Screen-Sharing APK Scam (AnyDesk/TeamViewer)
- **Trigger Conditions:** Remote desktop software (AnyDesk, RustDesk, TeamViewer QuickSupport) active during rapid UPI payment bursts or unauthorized QR debits.
- **Mandatory Action:** Instantly de-register mobile UPI VPAs, place temporary debit block on account, and notify customer via out-of-band call.
- **Urgency:** Immediate (< 15 minutes per RBI Digital Payment Security Directions).

## SOP-RBI-SIM-204: SIM-Swap Fraud & 24-Hour Telecom Cooling Window
- **Trigger Conditions:** Duplicate e-SIM or physical SIM reissuance reported by telecom provider within 24 hours prior to high-value IMPS/RTGS transfer or beneficiary addition.
- **Mandatory Action:** Enforce mandatory 24-hour IMPS/RTGS cooling freeze, revoke mobile NetBanking access token, and initiate verbal identity verification.
- **Urgency:** Immediate (< 15 minutes).

## SOP-AEPS-301: Aadhaar Micro-ATM Biometric Liveness Anomaly
- **Trigger Conditions:** Optical scanner static fingerprint reading (liveness score < 0.30) at Customer Service Point (CSP) kiosk > 100 km from account home branch.
- **Mandatory Action:** Enforce immediate biometric AEPS lock on Aadhaar number in UIDAI core integration and flag kiosk terminal ID to Law Enforcement (1930 Portal).
- **Urgency:** Immediate (< 30 minutes).
