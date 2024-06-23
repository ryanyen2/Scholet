The following steps was made to collect data:

1. Scrape profile data, 50 latest papers and 50 most cited papers having Google Scholar link:
   - Run `gs_profile_scraper_mongo.ipynb`
2. Collect papers abstracts:
   - Run `abstract_getter_mongo.ipynb`

To collect papers abstracts we check three sources and get the one which return the abstract first:

- OpenAlex API (limit 100.000 requests per day)
- Semantic Scholar API (limit 1rps)
- Scrape from Google Scholar
