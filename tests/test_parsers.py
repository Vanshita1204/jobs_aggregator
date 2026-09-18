"""Tests for the portal-specific search-results parsers, focused on
source_url canonicalization: the same posting scraped twice, with the
search engine's per-request tracking noise differing between the two
requests, must parse to the same `source_url` both times — otherwise
`create_job_records()`'s dedup (and the DB's UNIQUE constraint) never
catches it and every scrape inserts a fresh duplicate row.
"""

from bs4 import BeautifulSoup

from app.services.parsers import parse_hirist_jobs, parse_indeed_jobs, parse_linkedin_jobs


def _linkedin_html(href):
    return f"""
    <body><main>
        <section></section>
        <section><ul><li>
            <div>x</div>
            <div>
                <h3>Custom Software Engineer</h3>
                <h4>Accenture in India</h4>
                <span>Hyderabad, Telangana, India</span>
            </div>
            <a href="{href}"></a>
        </li></ul></section>
    </main></body>
    """


def test_parse_linkedin_jobs_strips_tracking_params():
    soup = BeautifulSoup(_linkedin_html(
        "https://in.linkedin.com/jobs/view/custom-software-engineer-at-accenture-in-india-4457503193"
        "?position=19&pageNum=0&refId=NfWS8hZuNE%2F9bjIM3PPh0Q%3D%3D&trackingId=TKz78SIKKSaXefC0ewkRYw%3D%3D"
    ), "html.parser")
    jobs = parse_linkedin_jobs(soup)
    assert len(jobs) == 1
    assert jobs[0]["source_url"] == (
        "https://in.linkedin.com/jobs/view/custom-software-engineer-at-accenture-in-india-4457503193"
    )


def test_parse_linkedin_jobs_same_posting_different_tracking_params_dedupes():
    """The real bug: the same LinkedIn job id scraped twice with different
    session tracking params must yield identical source_urls."""
    soup_a = BeautifulSoup(_linkedin_html(
        "https://in.linkedin.com/jobs/view/custom-software-engineer-at-accenture-in-india-4457503193"
        "?position=19&pageNum=0&refId=aaa&trackingId=111"
    ), "html.parser")
    soup_b = BeautifulSoup(_linkedin_html(
        "https://in.linkedin.com/jobs/view/custom-software-engineer-at-accenture-in-india-4457503193"
        "?position=17&pageNum=0&refId=bbb&trackingId=222"
    ), "html.parser")

    url_a = parse_linkedin_jobs(soup_a)[0]["source_url"]
    url_b = parse_linkedin_jobs(soup_b)[0]["source_url"]
    assert url_a == url_b


def _indeed_html(href, company="Acme", location="Bengaluru"):
    return f"""
    <table><tr>
        <td>
            <a href="{href}">Backend Engineer</a>
            <span data-testid="company-name">{company}</span>
            <span data-testid="text-location">{location}</span>
        </td>
    </tr></table>
    """


def test_parse_indeed_jobs_canonicalizes_jk_param():
    soup = BeautifulSoup(_indeed_html(
        "/rc/clk?jk=abc123&bb=e5MLZTI5WpLps_9QtBEfp&xkcb=SoCP67&fccid=150f3cf2b0531565&vjs=3"
    ), "html.parser")
    jobs = parse_indeed_jobs(soup)
    assert len(jobs) == 1
    assert jobs[0]["source_url"] == "https://in.indeed.com/viewjob?jk=abc123"


def test_parse_indeed_jobs_same_jk_different_tracking_noise_dedupes():
    soup_a = BeautifulSoup(_indeed_html("/rc/clk?jk=xyz789&bb=noiseA&xkcb=noiseA"), "html.parser")
    soup_b = BeautifulSoup(_indeed_html("/rc/clk?jk=xyz789&bb=noiseB&xkcb=noiseB"), "html.parser")

    url_a = parse_indeed_jobs(soup_a)[0]["source_url"]
    url_b = parse_indeed_jobs(soup_b)[0]["source_url"]
    assert url_a == url_b


def test_parse_indeed_jobs_leaves_url_unchanged_when_no_jk_present():
    soup = BeautifulSoup(_indeed_html("/viewjob-no-jk-param"), "html.parser")
    jobs = parse_indeed_jobs(soup)
    assert jobs[0]["source_url"] == "https://in.indeed.com/viewjob-no-jk-param"


def _hirist_html(href):
    return f"""
    <div class="joblist-card-v2">
        <div data-testid="job_title">Trantor Software - Senior .NET Developer</div>
        <div data-testid="job_location">Pune</div>
        <a href="{href}"></a>
    </div>
    """


def test_parse_hirist_jobs_strips_tracking_params():
    soup = BeautifulSoup(_hirist_html("/j/trantor-software-senior-net-developer-1665191?ref=sp_prm&jobPos=1"), "html.parser")
    jobs = parse_hirist_jobs(soup)
    assert len(jobs) == 1
    assert jobs[0]["source_url"] == "https://www.hirist.tech/j/trantor-software-senior-net-developer-1665191"


def test_parse_hirist_jobs_same_posting_different_rank_dedupes():
    soup_a = BeautifulSoup(_hirist_html("/j/trantor-software-senior-net-developer-1665191?ref=sp_prm&jobPos=1"), "html.parser")
    soup_b = BeautifulSoup(_hirist_html("/j/trantor-software-senior-net-developer-1665191?ref=sp&jobPos=5"), "html.parser")

    url_a = parse_hirist_jobs(soup_a)[0]["source_url"]
    url_b = parse_hirist_jobs(soup_b)[0]["source_url"]
    assert url_a == url_b
