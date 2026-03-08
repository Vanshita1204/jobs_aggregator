def parse_linkedin_jobs(soup):
    """Parse LinkedIn job postings from the soup object."""
    jobs = []
    return
    template = soup.select("body  main > section:nth-of-type(2) > ul > li")
    for job in template:
        data = job.select("div:nth-of-type(2)")[0]
        title = data.select_one("h3").text.strip() if data.select_one("h3") else "N/A"
        company = data.select_one("h4").text.strip() if data.select_one("h4") else "N/A"
        location = (
            data.select_one("span").text.strip() if data.select_one("span") else "N/A"
        )
        source_url = job.select("a")[0]["href"]
        print(f"Title: {title}, Company: {company}, Location: {location}")
        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "source": "LinkedIn",
                "source_url": source_url,
            }
        )
    return jobs


def parse_indeed_jobs(soup):
    """Parse Indeed job postings from the soup object."""
    jobs = []
    breakpoint()
    template = soup.select("td")
    for job in template:
        title = job.select("a")[0].text.strip() if job.select("a")[0] else "N/A"
        company = (
            job.select_one('[data-testid="company-name"]').text.strip()
            if job.select_one('[data-testid="company-name"]')
            else "N/A"
        )
        location = (
            job.select_one('[data-testid="text-location"]').text.strip()
            if job.select_one('[data-testid="text-location"]')
            else "N/A"
        )
        source_url = "https://www.indeed.com" + job.select_one("a")["href"]
        print(f"Title: {title}, Company: {company}, Location: {location}, Source: Indeed")
        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "source": "Indeed",
                "source_url": source_url,
            }
        )
    return jobs


def parse_hirist_jobs(soup):
    """Parse Hirist job postings from the soup object."""
    jobs = []
    return
    template = soup.select("div.joblist-card-v2")
    for job in template:
        title = job.select_one('[data-testid="job_title"]')
        location = job.select_one('[data-testid="job_location"]')
        link_el = job.select_one("a[href]")
        if not (title and location and link_el):
            continue
        data = title.get_text(strip=True)
        title = data.split(" - ")[1] if " - " in data else data
        company = data.split(" - ")[0]
        location = location.get_text(strip=True)
        job_url = "https://www.hirist.tech" + link_el["href"]
        print(f"Title: {title}, Company: {company}, Location: {location}, Source: Hirist")

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "source_url": job_url,
                "source": "Hirist",
            }
        )
    return jobs
