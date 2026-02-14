def parse_linkedin_jobs(soup):
    """Parse LinkedIn job postings from the soup object."""
    jobs = []
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
