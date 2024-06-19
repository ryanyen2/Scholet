import time
import os
import requests
from tqdm import tqdm
from helpers import ExtensibleArray
import random
import bs4
from playwright.sync_api import sync_playwright
from config import db

papers_collection = db["papers"]

API_KEY_SEMANTIC_SCHOLAR = os.getenv("API_KEY_SEMANTIC_SCHOLAR")


class GoogleScholarScrapper:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    def __get_html_content(self, url):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(self.USER_AGENTS)
                )
                page = context.new_page()
                page.goto(url)
                page.wait_for_load_state("load")

                # Random scrolling to mimic human behavior
                for _ in range(random.randint(1, 3)):
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight/3);")
                    page.wait_for_timeout(
                        random.randint(1000, 3000)
                    )  # Wait between 1 to 3 seconds

                html_content = page.content()
                context.close()
                browser.close()
        except Exception as e:
            print(f"Error while fetching {url}: {e}")
            html_content = None

        return html_content

    def get_abstract_from_gs(self, gs_url):
        soup = bs4.BeautifulSoup(self.__get_html_content(gs_url), "lxml")
        # html_content_pretty = soup.prettify()
        # print(html_content_pretty)
        description = soup.find("div", {"id": "gsc_oci_descr"})
        if not description:
            description = soup.find("div", {"class": "gsh_small"})
        if not description:
            description = soup.find("div", {"class": "gsh_csp"})

        if description:
            description = description.get_text()

        time.sleep(random.randint(10, 15))  # Random delay between 10 to 15 seconds
        return str(description)


class PublicationAbstractGetter:
    def __init__(self):
        self.scraper = GoogleScholarScrapper()

    def process_title(self, title):
        return (
            title.replace("-", " ")
            .replace(",", "")
            .replace(":", "")
            .replace(".", "")
            .replace("’", "")
            .replace("&", " ")
            .replace('"', "")
            .replace("'", "")
        )

    def get_data_by_title_year_openalex(self, title, year):
        try:
            if year:
                url = f'https://api.openalex.org/works?filter=title.search:"{title}",publication_year:{year}'
            else:
                url = f'https://api.openalex.org/works?filter=title.search:"{title}"'
            response = requests.get(url)
            for paper in response.json()["results"]:
                if title.lower().replace(" ", "") in self.process_title(
                    paper["title"]
                ).lower().replace(" ", ""):
                    print("_" * 40)
                    print(title)
                    print(self.process_title(paper["title"]))
                    return paper
            return {}
        except Exception as e:
            print(title)
            print(e)
            try:
                print(response.json())
            except:
                print(response)
            return {}

    def get_data_by_title_year_semantic_scholar(self, title):
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query=title:({title})"
            query_params = {
                "fields": "paperId,title,abstract,venue,citationCount,referenceCount,url,year,authors.name",
                "limit": 10,
            }
            headers = {"x-api-key": API_KEY_SEMANTIC_SCHOLAR}

            papers = []

            time.sleep(1)
            # semantic scholar API limit is 100 requests per 5 minutes without key
            # with the key is 10RPS
            response = requests.get(url, params=query_params, headers=headers)

            response_data = response.json()
            papers = response_data["data"]

            for paper in papers:
                print("_" * 40)
                print(title)
                print(self.process_title(paper["title"]))
                if title.lower().replace(" ", "") in self.process_title(
                    paper["title"]
                ).lower().replace(" ", ""):
                    return paper
            return {}
        except Exception as e:
            print(title)
            print(e)
            print(response_data)
            return {}

    def get_abstract(self, abstract_inverted_index):
        try:
            abstract_list = ExtensibleArray()
            for word, positions in abstract_inverted_index.items():
                for position in positions:
                    abstract_list.set_value(position, word)
            abstract = " ".join(abstract_list.get_array())
        except:
            abstract = None
        return abstract

    def is_publication_in_current_abstracts(self, title, year, authorID):
        return papers_collection.find_one(
            {"title": title, "year": year, "authorID": authorID}
        )

    def safe_compare(self, a, b):
        if a is None and b is None:
            return False
        if a is None:
            return False
        if b is None:
            return True
        return a > b

    def fetch_existing_publications_by_author(self, author_id):
        return list(papers_collection.find({"authorID": author_id}))

    def fetch_publication_abstracts(self, publications, profile_info) -> None:
        author_id = profile_info["authorID"]

        existing_publications = self.fetch_existing_publications_by_author(author_id)
        existing_publication_set = {
            (pub["title"], pub["year"]) for pub in existing_publications
        }

        for pub in publications:
            title = pub["title"]
            year = pub["year"]
            cited_by = pub["cited_by"]

            if (title, year) in existing_publication_set:
                # Publication already exists, skip it
                continue
            # existing_pub = self.is_publication_in_current_abstracts(
            #     title, year, author_id
            # )
            # if existing_pub:
            #     if existing_pub["abstract"]:
            #         # print(f"Publication '{title}' from year {year} already exists.")
            #         continue

            semantic_scholar_url = None
            doi = None
            abstract = None

            abstract, source, doi = self.retrieve_abstract_openalex(title, year)
            if not abstract:
                abstract, source, semantic_scholar_url = (
                    self.retrieve_abstract_semantic_scholar(title)
                )
            if not abstract:
                source = "GoogleScholar"
                abstract = self.scraper.get_abstract_from_gs(
                    f"https://scholar.google.com/citations?{pub['url']}"
                )

            new_pub_data = {
                "title": title,
                "gs_url": f"https://scholar.google.com/citations?{pub['url']}",
                "abstract": abstract,
                "doi": doi,
                "semantic_scholar": semantic_scholar_url,
                "cited_by": cited_by,
                "year": year,
                "authorID": author_id,
                "source": source,
            }

            print(f"Updated: {title}")
            papers_collection.update_one(
                {"title": title, "year": year, "authorID": author_id},
                {"$set": new_pub_data},
                upsert=True,
            )

    def retrieve_abstract_openalex(self, title, year):
        data = self.get_data_by_title_year_openalex(self.process_title(title), year)

        abstract = self.get_abstract(data.get("abstract_inverted_index"))
        doi = data.get("doi")
        return abstract, "OpenAlex", doi

    def retrieve_abstract_semantic_scholar(self, title):
        data = self.get_data_by_title_year_semantic_scholar(self.process_title(title))
        abstract = data.get("abstract")
        semantic_scholar_url = data.get("url")
        return abstract, "SemanticScholar", semantic_scholar_url

    def update_abstracts(self, profile_info):
        self.fetch_publication_abstracts(profile_info["publications"], profile_info)
        self.fetch_publication_abstracts(
            profile_info["publications_pubdate"], profile_info
        )


scraper = PublicationAbstractGetter()

profiles_collection = db["profiles"]
profiles = profiles_collection.find()
for doc in tqdm(list(profiles)):
    scraper.update_abstracts(doc)
