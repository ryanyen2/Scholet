The following steps was made to collect data:

1. Scrape profile data, 20 latest papers and 20 most cited papers having Google Scholar link:
   - Run `gs_profile_scraper.ipynb`
2. Collect papers abstracts using OpenAlex API:
   - Run `openalex_abstracts_getter.ipynb`
3. Scrape missing abstracts from Google Scholar:
   - Run `gs_abstracts_scraper.ipynb`
