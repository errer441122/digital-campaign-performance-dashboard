from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_sql_evidence_and_requirements_are_reviewer_visible() -> None:
    required_paths = [
        "requirements.txt",
        "sql/SQL_EVIDENCE.md",
        "sql/marketing_analytics_evidence.sql",
    ]

    for relative_path in required_paths:
        path = ROOT / relative_path
        assert path.exists(), f"{relative_path} should be committed at repository root"

    readme = read_text("README.md")
    assert "`sql/SQL_EVIDENCE.md`" in readme
    assert "`sql/marketing_analytics_evidence.sql`" in readme
    assert "../sql/" not in readme

    evidence = read_text("sql/SQL_EVIDENCE.md")
    assert evidence.count("## Query ") == 10
    for required in [
        "data/campaign_performance_sample.csv",
        "data/landing_page_sample.csv",
        "data/ab_test_conversion_sample.csv",
        "ROW_NUMBER() OVER",
        "Contact-To-Conversion Funnel",
        "Attribution",
        "CRM Lifecycle",
    ]:
        assert required in evidence
