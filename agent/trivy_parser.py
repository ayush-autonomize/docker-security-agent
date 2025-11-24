"""Parse Trivy JSON reports and extract vulnerabilities."""
from typing import Any, Dict, List


def parse_trivy_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse a Trivy JSON report and return a flat list of vulnerabilities.

    This supports Trivy's typical JSON structure with a top-level "Results" list,
    each having a "Vulnerabilities" list.
    """
    findings = []
    results = report.get("Results") or report.get("results") or []
    for res in results:
        vulns = res.get("Vulnerabilities") or res.get("vulnerabilities") or []
        for v in vulns:
            findings.append(v)
    return findings
