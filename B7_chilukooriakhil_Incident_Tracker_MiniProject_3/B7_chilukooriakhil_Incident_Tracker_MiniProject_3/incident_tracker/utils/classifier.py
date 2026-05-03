from __future__ import annotations

import re


NETWORK_PATTERN = re.compile(
    r"\b(?:\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?|tcp|udp|icmp|vlan|switch|firewall|dns|router|packet\s+loss|network)\b",
    re.IGNORECASE,
)
SECURITY_PATTERN = re.compile(
    r"\b(?:breach|ransomware|brute[- ]force|malware|phishing|unauthori[sz]ed|threat|suspicious\s+login)\b",
    re.IGNORECASE,
)
APP_PATTERN = re.compile(
    r"\b(?:error\s*code|exception|stack\s*trace|nullpointerexception|valueerror|http[- ]?\d{3}|api|service|gateway|job\s+failed)\b",
    re.IGNORECASE,
)

CRITICAL_PATTERN = re.compile(
    r"\b(?:outage|down|offline|breach|ransomware)\b|(?<!non-)(?<!non )\bproduction\b",
    re.IGNORECASE,
)
HIGH_PATTERN = re.compile(
    r"\b(?:timeout|failing|unavailable|unreachable|suspicious)\b",
    re.IGNORECASE,
)
MEDIUM_PATTERN = re.compile(
    r"\b(?:slow|degraded|warning|intermittent)\b",
    re.IGNORECASE,
)

IP_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?\b", re.IGNORECASE)
PROTOCOL_PATTERN = re.compile(r"\b(?:TCP|UDP|ICMP)\b", re.IGNORECASE)
HOST_PATTERN = re.compile(r"\b[a-z0-9][a-z0-9-]*\d+\b", re.IGNORECASE)
ERROR_CODE_PATTERN = re.compile(r"\b(?:[A-Z]{2,}-\d{2,5}|error\s*code[:#]?\s*[A-Z]?\d+)\b", re.IGNORECASE)
HTTP_STATUS_PATTERN = re.compile(r"\bHTTP[- ]?\d{3}\b", re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(
    r"\b(?:NullPointerException|ValueError|TypeError|TimeoutError|RuntimeError)\b",
    re.IGNORECASE,
)
THREAT_PATTERN = re.compile(
    r"\b(?:breach|ransomware|brute[- ]force|malware|phishing|unauthori[sz]ed)\b",
    re.IGNORECASE,
)
SERVICE_NAME_PATTERN = re.compile(
    r"\b([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z0-9-]+)*)\s+(?:service|api|gateway)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_type(text: str) -> str:
    normalized = _normalize(text)

    if SECURITY_PATTERN.search(normalized):
        return "security"
    if NETWORK_PATTERN.search(normalized):
        return "network"
    if APP_PATTERN.search(normalized):
        return "app"
    return "general"


def detect_severity(text: str) -> str:
    normalized = _normalize(text)

    if CRITICAL_PATTERN.search(normalized):
        return "critical"
    if HIGH_PATTERN.search(normalized):
        return "high"
    if MEDIUM_PATTERN.search(normalized):
        return "medium"
    return "low"
