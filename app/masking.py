import re
from typing import Dict, Any, Tuple, Union
from copy import deepcopy

class PIIMasker:
    """
    PII Protection Module (masking.py in Enterprise Architecture):
    Redacts and tokenizes sensitive customer PII before sending payloads
    to Tachyon LLM endpoints (gpt5.1, gemini-2.5-pro) to comply with
    banking privacy and PCI-DSS / GLBA regulations.
    """
    # Regex patterns for financial & personal identifiers
    CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
    SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    PHONE_REGEX = re.compile(r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})')
    ACCOUNT_REGEX = re.compile(r'\bACT-([0-9]{4})-([0-9]{4})\b')
    ECN_REGEX = re.compile(r'\b(?:ECN|CUST)-([0-9]{6})\b')

    @classmethod
    def mask_text(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Masks raw text strings and returns the redacted string
        along with a private token map for reverse de-tokenization if needed.
        """
        if not text:
            return text, {}

        token_map: Dict[str, str] = {}

        # 1. Mask Email
        def mask_email_match(m):
            original = m.group(0)
            user, domain = original.split('@', 1)
            masked = f"{user[0]}***{user[-1] if len(user) > 1 else ''}@{domain}"
            token_map[masked] = original
            return masked

        masked = cls.EMAIL_REGEX.sub(mask_email_match, text)

        # 2. Mask Phone numbers
        def mask_phone_match(m):
            original = m.group(0)
            masked = "+1-***-***-" + m.group(3)
            token_map[masked] = original
            return masked

        masked = cls.PHONE_REGEX.sub(mask_phone_match, masked)

        # 3. Mask SSN
        def mask_ssn_match(m):
            original = m.group(0)
            masked = "***-**-" + original[-4:]
            token_map[masked] = original
            return masked

        masked = cls.SSN_REGEX.sub(mask_ssn_match, masked)

        # 4. Mask PAN / Credit Card
        def mask_card_match(m):
            digits = re.sub(r'\D', '', m.group(0))
            if 13 <= len(digits) <= 16:
                masked = f"{digits[:4]}-****-****-{digits[-4:]}"
                token_map[masked] = m.group(0)
                return masked
            return m.group(0)

        masked = cls.CARD_REGEX.sub(mask_card_match, masked)

        # 5. Mask Account Numbers
        def mask_act_match(m):
            original = m.group(0)
            masked = f"ACT-****-{m.group(2)}"
            token_map[masked] = original
            return masked

        masked = cls.ACCOUNT_REGEX.sub(mask_act_match, masked)

        # 6. Mask Customer ECN
        def mask_ecn_match(m):
            original = m.group(0)
            masked = f"ECN-***{m.group(1)[-3:]}"
            token_map[masked] = original
            return masked

        masked = cls.ECN_REGEX.sub(mask_ecn_match, masked)

        return masked, token_map

    @classmethod
    def mask_payload(cls, data: Any) -> Tuple[Any, Dict[str, str]]:
        """
        Recursively masks dict, list, or primitive JSON payloads.
        """
        aggregated_tokens: Dict[str, str] = {}

        if isinstance(data, str):
            masked, tokens = cls.mask_text(data)
            aggregated_tokens.update(tokens)
            return masked, aggregated_tokens

        elif isinstance(data, dict):
            masked_dict = {}
            for k, v in data.items():
                # Specific sensitive key sanitization
                if k.lower() in ["customer_name", "full_name"]:
                    val_str = str(v)
                    parts = val_str.split()
                    masked_name = f"{parts[0][0]}. {parts[-1][0]}. [Customer]" if len(parts) > 1 else "C. [Customer]"
                    aggregated_tokens[masked_name] = val_str
                    masked_dict[k] = masked_name
                else:
                    masked_val, tokens = cls.mask_payload(v)
                    aggregated_tokens.update(tokens)
                    masked_dict[k] = masked_val
            return masked_dict, aggregated_tokens

        elif isinstance(data, list):
            masked_list = []
            for item in data:
                masked_item, tokens = cls.mask_payload(item)
                aggregated_tokens.update(tokens)
                masked_list.append(masked_item)
            return masked_list, aggregated_tokens

        return data, aggregated_tokens
