import json
from pathlib import Path

from agent.trivy_parser import parse_trivy_report


def test_parse_trivy_report_finds_vulns():
    fixture = Path(__file__).parent / "fixtures" / "trivy_report_sample.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    findings = parse_trivy_report(data)
    assert isinstance(findings, list)
    assert len(findings) == 1
    assert findings[0]["VulnerabilityID"] == "CVE-2020-1234"
