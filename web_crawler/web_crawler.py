import queue
import re
import requests

from bs4 import BeautifulSoup

class URL:
    """URL class"""

    def __init__(self, url: str, parent_url = None) -> None:
        # Absolute URLs
        # Full URL
        if re.search(r"^https?://", url, re.I):
            self.protocol, rest = url.split("//", maxsplit=1)
            self.protocol = self.protocol + "//"
            if '/' in rest:
                self.domain, self.section = rest.split("/", maxsplit=1)
                self.section = "/" + self.section
            else:
                self.domain = rest
                self.section = "/"

        # Hidden protocol
        elif url.startswith("//"):
            self.protocol = parent_url.protocol
            url = url.removeprefix("//")
            self.domain, self.section = url.split("/", maxsplit=1)
            self.section = "/" + self.section

        # Hidden domain
        elif url.startswith("/"):
            self.protocol = parent_url.protocol
            self.domain = parent_url.domain
            self.section = url

        # Relative URLs
        else:
            self.protocol = parent_url.protocol
            self.domain = parent_url.domain
            self.section = parent_url.section + "/" + url
        
        self.full = self.protocol + self.domain + self.section

class WebCrawler:
    """Web crawler class"""

    def __init__(self, domain: str) -> None:
        self.domain = domain

        self.found_url_amount = 0
        self.take_away_url_amount = 0

        self.processed_url = set()
        self.subdomains = set()
        self.take_away_domain = set()
        self.pdf_files = set()
        self.doc_files = set()
        self.docx_files = set()

        self.visited_url = set()
        self.bad_url = set()
        self.unresponsive_url = set()
        
        self.url_queue = queue.Queue()
        self.second_chance = True
    
    def process_url(self, url: URL) -> None:
        if url.full not in self.processed_url:
            self.processed_url.add(url.full)

            if url.section.endswith(".pdf"):
                self.pdf_files.add(url.full)

            elif url.section.endswith(".docx"):
                self.docx_files.add(url.full)

            elif url.section.endswith(".doc"):
                self.doc_files.add(url.full)

            elif url.domain.find('.' + self.domain) != -1:
                self.subdomains.add(url.domain)
            
            elif url.domain == self.domain:
                self.url_queue.put(url)

            else:
                self.take_away_url_amount += 1
                self.take_away_domain.add(url.domain)
    
    def save_html(self, file_name: str, html: str) -> None:
        with open("./pages/" + file_name + ".html", 'w', encoding="utf-8") as fp:
            fp.write(html)
    
    def save_stats(self) -> None:
        with open("./stats/" + self.domain + "_stats.txt", 'w', encoding="utf-8") as fp:
            fp.write("Domain: " + self.domain + '\n')
            fp.write("URLs found: " + str(self.found_url_amount) + "\n")
            fp.write("URLs visited: " + str(len(self.visited_url)) + "\n")
            fp.write("Subdomains: " + str(len(self.subdomains)) + "\n")
            fp.write("Bad URLs: " + str(len(self.bad_url)) + "\n")
            fp.write("Take away URLs: " + str(self.take_away_url_amount) + "\n")
            fp.write("PDF files: " + str(len(self.pdf_files)) + "\n")
            fp.write("Doc files: " + str(len(self.doc_files)) + "\n")
            fp.write("Docx files: " + str(len(self.docx_files)) + "\n")
        
        with open("./stats/" + self.domain + "_processed_url.txt", 'w', encoding="utf-8") as fp:
            for ref in self.processed_url:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_visited_url.txt", 'w', encoding="utf-8") as fp:
            for ref in self.visited_url:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_subdomains.txt", 'w', encoding="utf-8") as fp:
            for ref in self.subdomains:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_bad_url.txt", 'w', encoding="utf-8") as fp:
            for ref in self.bad_url:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_take_away_domain.txt", 'w', encoding="utf-8") as fp:
            for ref in self.take_away_domain:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_pdf_files.txt", 'w', encoding="utf-8") as fp:
            for ref in self.pdf_files:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_doc_files.txt", 'w', encoding="utf-8") as fp:
            for ref in self.doc_files:
                fp.write(ref + '\n')
        
        with open("./stats/" + self.domain + "_docx_files.txt", 'w', encoding="utf-8") as fp:
            for ref in self.docx_files:
                fp.write(ref + '\n')

    def save_url(self, url) -> None:
        with open("current_url.txt", 'w', encoding="utf-8") as fp:
            fp.write(url)

    def start_crawling(self, start_url: str, page_amount_to_visit: int) -> None:
        if start_url is not None:
            self.process_url(URL(start_url))

        while not self.url_queue.empty() and len(self.visited_url) <= page_amount_to_visit:
            url = self.url_queue.get()
            self.save_url(url.full)

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.34'}
            
            try:
                resp = requests.get(url.full, headers=headers, timeout=(5, 30))
            except:
                self.unresponsive_url.add(url)
                continue

            if resp.status_code == requests.codes.ok:
                self.visited_url.add(url.full)

                if len(self.visited_url) % 1000 == 0:
                    self.save_stats()
            
                if len(self.visited_url) % 100 == 0:
                    print(len(self.visited_url))

                try:
                    root = BeautifulSoup(resp.text, features="lxml")
                except:
                    continue

                #self.save_html(str(hash(url.domain + url.section)), str(root))

                for link in root.find_all('a'):
                    href = link.get("href")

                    if href:
                        self.found_url_amount += 1

                        if not re.search(r"^(mailto|tel|ftp|file):", href, re.I):
                            self.process_url(URL(href, url))
            else:
                self.bad_url.add(url.full)
        
        if self.second_chance:
            self.second_chance = False

            for url in self.unresponsive_url:
                self.url_queue.put(url)
            
            self.start_crawling(None)