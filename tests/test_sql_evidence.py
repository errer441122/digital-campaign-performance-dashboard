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


def test_every_sql_evidence_query_runs_and_returns_rows(monkeypatch) -> None:
    """The SQL file is evidence only if it executes: run each query in DuckDB."""
    import duckdb

    monkeypatch.chdir(ROOT)  # queries use repo-relative paths like 'data/...'
    queries = [q for q in read_text("sql/marketing_analytics_evidence.sql").split("-- Query ")[1:]]
    assert len(queries) == 10
    for q in queries:
        title, _, body = q.partition("\n")
        rows = duckdb.sql(body).fetchall()
        assert rows, f"Query {title.strip()} returned no rows"
