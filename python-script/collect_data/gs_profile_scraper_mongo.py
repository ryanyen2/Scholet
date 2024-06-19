import requests, bs4, re, time
import os
import pandas as pd
from config import db

profiles_collection = db["profiles"]


class Author(object):
    def __init__(
        self,
        authorID,
        name=None,
        image_link=None,
        interests=None,
        citations=None,
        hindex=None,
        i10index=None,
        citation_histogram=None,
        coauthors=None,
        publications=None,
        publications_pubdate=None,
        all_publications_retrieved=False,
        all_publications_extracted=False,
        cstart=0,
        pagesize=50,  # 100 is Max page size in scholar
        cookies=None,
    ):

        self.cstart = cstart
        self.pagesize = pagesize
        self.cookies = cookies
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }

        self.soup = None

        self.authorID = authorID
        self.name = name
        self.image_link = image_link
        self.interests = interests
        self.citations = citations
        self.hindex = hindex
        self.i10index = i10index
        self.citation_histogram = citation_histogram
        self.coauthors = coauthors
        self.publications = publications
        self.publications_pubdate = publications_pubdate
        self.all_publications_retrieved = all_publications_retrieved
        self.all_publications_extracted = all_publications_extracted

    def set_url(self):
        return f"https://scholar.google.com/citations?hl=en&user={self.authorID}&cstart={self.cstart}&pagesize={self.pagesize}"

    def set_url_sortby_pubdate(self):
        return f"https://scholar.google.com/citations?hl=en&user={self.authorID}&cstart={self.cstart}&pagesize={self.pagesize}&sortby=pubdate"

    def make_profile_request(self, custom_url=""):
        url = custom_url if len(custom_url) != 0 else self.set_url()
        print(url)
        time.sleep(15)
        response = requests.request(
            "GET", url, headers=self.headers, cookies=self.cookies
        )
        if response.status_code == 429:
            raise Exception(
                "The server responded with Error 429. We have been detected. Wait before trying again."
            )
        self.cookies = response.cookies
        return response

    def get_soup(self):
        self.soup = bs4.BeautifulSoup(
            self.make_profile_request().content, "html.parser"
        )

    def make_coauthor_request(self):
        url = self.set_url() + "&view_op=list_colleagues"
        time.sleep(15)
        response = requests.request("GET", url, headers=self.headers)
        if response.status_code == 429:
            raise Exception(
                "The server responded with Error 429. We have been detected. Wait before trying again."
            )
        return response

    def get_full_name(self):
        name = self.soup.find("div", {"id": "gsc_prf_in"})
        if name:
            self.name = name.get_text()

    def get_image_link(self):
        image = self.soup.find("img", {"id": "gsc_prf_pup-img"})
        if image:
            self.image_link = image.get("src")

    def get_interests(self):
        self.interests = list(
            map(
                lambda x: x.get_text(),
                self.soup.find_all("a", {"class": "gsc_prf_inta"}),
            )
        )

    def get_citations_count(self, citation_info):
        citation = citation_info.find(
            "a", text=re.compile("Citations"), attrs={"class": "gsc_rsb_f"}
        )
        if citation:
            citation_value = citation.parent.parent.find_all(
                "td", {"class": "gsc_rsb_std"}
            )
            if len(citation_value) > 0:
                self.citations = int(citation_value[0].get_text())

    def get_hindex(self, citation_info):
        hindex = citation_info.find(
            "a", text=re.compile("h-index"), attrs={"class": "gsc_rsb_f"}
        )
        if hindex:
            hindex_value = hindex.parent.parent.find_all("td", {"class": "gsc_rsb_std"})
            if len(hindex_value) > 0:
                self.hindex = int(hindex_value[0].get_text())

    def get_i10index(self, citation_info):
        i10index = citation_info.find(
            "a", text=re.compile("i10-index"), attrs={"class": "gsc_rsb_f"}
        )
        if i10index:
            i10index_value = i10index.parent.parent.find_all(
                "td", {"class": "gsc_rsb_std"}
            )
            if len(i10index_value) > 0:
                self.i10index = int(i10index_value[0].get_text())

    def get_citation_metrics(self):
        citation_info = self.soup.find("div", {"id": "gsc_rsb_cit"})
        if citation_info:
            self.get_citations_count(citation_info)
            self.get_hindex(citation_info)
            self.get_i10index(citation_info)

    def get_citation_histogram(self):
        citation_hist = self.soup.find_all("div", {"class": "gsc_md_hist_w"})
        if citation_hist:
            citation_hist = citation_hist[0]
            citation_hist_time = list(
                map(
                    lambda x: x.get_text(),
                    citation_hist.find_all("span", {"class": "gsc_g_t"}),
                )
            )
            citation_hist_cites = list(
                map(
                    lambda x: x.get_text(),
                    citation_hist.find_all("a", {"class": "gsc_g_a"}),
                )
            )
            self.citation_histogram = [
                {"year": year, "citations": citations}
                for year, citations in zip(citation_hist_time, citation_hist_cites)
            ]

    def get_coauthors(self):
        coauthor_list = self.soup.find("div", {"id": "gsc_rsb_co"})
        if coauthor_list:
            if coauthor_list.find("button"):  # too many coauthors requires a request
                coauthor_list = bs4.BeautifulSoup(
                    self.make_coauthor_request().content, "html.parser"
                ).find("div", {"id": "gsc_codb_content"})
                coauthor_list = coauthor_list.find_all("div", {"class": "gsc_ucoar"})
                coauthor_ids = list(
                    map(lambda x: x.get("id").split("-")[-1], coauthor_list)
                )
                coauthor_names = list(
                    map(lambda x: x.find("img").get("alt"), coauthor_list)
                )
                self.coauthors = list(zip(coauthor_ids, coauthor_names))
            else:
                coauthor_list = coauthor_list.find_all("img")
                coauthor_ids = list(
                    map(lambda x: x.get("id").split("-")[1], coauthor_list)
                )
                coauthor_names = list(map(lambda x: x.get("alt"), coauthor_list))
                self.coauthors = list(zip(coauthor_ids, coauthor_names))

    def extract_compact_publication(self, publication_element):
        title = publication_element.find("a", {"class": "gsc_a_at"}).get_text()
        year = (
            publication_element.find("td", {"class": "gsc_a_y"})
            .find("span", {"class": "gsc_a_hc"})
            .get_text()
        )
        if year:
            year = int(year)
        else:
            year = None
        url = (
            publication_element.find("a", {"class": "gsc_a_at"})
            .get("href")
            .split("?")[-1]
        )
        cited_by = publication_element.find("a", {"class": "gsc_a_ac"}).get_text()
        if cited_by:
            cited_by = int(cited_by)
        else:
            cited_by = None
        return {"title": title, "year": year, "cited_by": cited_by, "url": url}

    def get_publications_list(self):
        publication_list = []

        items = self.soup.find_all("tr", {"class": "gsc_a_tr"})
        publication_list += items
        self.publications = list(
            map(lambda x: self.extract_compact_publication(x), publication_list)
        )

        publication_pubdate_list = []
        url_sortby_pubdate = self.set_url_sortby_pubdate()

        soup = bs4.BeautifulSoup(
            self.make_profile_request(custom_url=url_sortby_pubdate).content,
            "html.parser",
        )
        items = soup.find_all("tr", {"class": "gsc_a_tr"})
        publication_pubdate_list += items
        self.publications_pubdate = list(
            map(lambda x: self.extract_compact_publication(x), publication_pubdate_list)
        )

    def get_publications_detail(self):
        unscraped_publications = filter(
            lambda x: not x.get("detail_extracted", False), self.publications
        )
        for publication in unscraped_publications:
            successful = publication.scrape()
            if not successful:
                break
        self.set_all_publications_extracted()

    def set_all_publications_extracted(self):
        checker = next(
            filter(lambda x: not x.get("detail_extracted", False), self.publications),
            None,
        )
        if checker is None:
            self.all_publications_extracted = True
        else:
            self.all_publications_extracted = False

    def save_data_mongo(self):
        data = self.export_json()
        profiles_collection.update_one(
            {"authorID": data["authorID"]},
            {"$set": data},
            upsert=True,
        )

    def export_json(self):
        data = {
            "authorID": self.authorID,
            "name": self.name,
            "image_link": self.image_link,
            "interests": self.interests,
            "citations": self.citations,
            "hindex": self.hindex,
            "i10index": self.i10index,
            "citation_histogram": self.citation_histogram,
            "publications": [],
            "all_publications_retrieved": self.all_publications_retrieved,
            "all_publications_extracted": self.all_publications_extracted,
            "cstart": self.cstart,
            "pagesize": self.pagesize,
        }
        data["publications"] = self.publications
        data["publications_pubdate"] = self.publications_pubdate
        return data

    def scrape(self):
        if not self.all_publications_retrieved:
            self.get_soup()
            self.get_full_name()
            self.get_image_link()
            self.get_interests()
            self.get_citation_metrics()
            self.get_citation_histogram()
            self.get_publications_list()


def create_author_mongo(authorID):
    return Author(authorID)


df = pd.read_excel(
    "raw_data/Waterloo_AI_Faculty_Email_List_edited.xlsx",
    usecols=[
        "email",
        "first_name",
        "last_name",
        "faculty",
        "department",
        "area_of_focus",
        "gs_link",
        "gs_author_id",
    ],
)

for gs_author_id in df["gs_author_id"]:
    if type(gs_author_id) == str:
        author_obj = create_author_mongo(gs_author_id)
        author_obj.scrape()
        author_obj.save_data_mongo()
