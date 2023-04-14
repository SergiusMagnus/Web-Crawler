import queue
import re
import requests

from bs4 import BeautifulSoup

class URL:
    """URL class"""

    def __init__(self, url: str = None, domain: str = None, section: str = "/", protocol: str = "https://") -> None:
        if url is not None:
            self.protocol = protocol
            self.domain = ""
            self.section = section

            protocol = re.search(r"https?://", url)
            if protocol:
                self.protocol = protocol.group()

            domain = re.search(r"[\w.-]*", url.removeprefix(self.protocol))
            if domain:
                self.domain = domain.group()
        
            section = url.removeprefix(self.protocol).removeprefix(self.domain)
            if re.search(r"[\w-]", section):
                self.section = section
        else:
            self.protocol = protocol
            self.domain = domain
            self.section = section
    
    def get_full_address(self) -> str:
        return self.protocol + self.domain + self.section

class WebCrawler:
    """Web crawler class"""

    def __init__(self, domain: str) -> None:
        self.base_domain = domain
        self.visited_url = set()
        self.processed_url_counter = 0
        self.processed_url = set()
        self.inner_url = dict()
        self.bad_url = set()
        self.subdomains = set()
        self.take_away_url_counter = 0
        self.take_away_url = set()
        self.files = set()

        self.unanswered_url = set()
        self.unparsed_url = set()

        self.url_queue = queue.Queue()
    
    def process_url(self, url: URL) -> bool:
        self.processed_url_counter += 1

        if url.domain + url.section not in self.processed_url:
            self.processed_url.add(url.domain + url.section)

            if re.search(r"([.](pdf|doc|docx))$", url.section, re.I):
                self.files.add(url.domain + url.section)
            elif re.search(self.base_domain, url.domain):
                self.url_queue.put(url)
                self.subdomains.add(url.domain)
                self.inner_url.setdefault(url.domain, set()).add(url.section)
            else:
                self.take_away_url_counter += 1
                self.take_away_url.add(url.domain)
            return True
        else:
            return False
    
    def save_html(self, file_name: str, html: str) -> None:
        with open("./pages/" + file_name + ".html", 'w', encoding="utf-8") as fp:
            fp.write(html)
    
    def save_stats(self) -> None:
        with open("./stats/" + self.base_domain + ".txt", 'w', encoding="utf-8") as fp:
            fp.write("Основной домен: " + self.base_domain + '\n')
            fp.write("Встречено ссылок: " + str(self.processed_url_counter) + "\n")
            # fp.write("Уникальные ссылки:\n")  
            # for ref in self.processed_url:
            #     fp.write('\t' + ref + '\n')

            fp.write("Посещено уникальных страниц: " + str(len(self.visited_url)) + "\n")
            # fp.write("Посещенные уникальные страницы:\n")  
            # for ref in self.visited_url:
            #     fp.write('\t' + ref + '\n')

            fp.write("Встречено поддоменов: " + str(len(self.subdomains)) + "\n")
            # fp.write("Встреченные поддомены:\n")  
            # for ref in self.subdomains:
            #     fp.write('\t' + ref + '\n')

            fp.write("Количество неработающих ссылок: " + str(len(self.bad_url)) + "\n")
            # fp.write("Неработающие ссылки:\n")  
            # for ref in self.bad_url:
            #     fp.write('\t' + ref + '\n')
            
            num = 0
            for s in self.inner_url.values():
                num += len(s)
            fp.write("Количество внутренних страниц: " + str(num) + "\n")

            # for key, value in self.inner_url.items():
            #     fp.write("Домен: " + key + "\n")
            #     for ref in value:
            #         fp.write("\t" + ref + "\n")

            fp.write("Общее число ссылок на внешние ресурсы: " + str(self.take_away_url_counter) + "\n")
            # fp.write("Уникальные внешние ресурсы:\n")
            # for ref in self.take_away_url:
            #     fp.write('\t' + ref + '\n')

            fp.write("Общее число ссылок на файлы pdf/doc/docx: " + str(len(self.files)) + "\n")
            # fp.write("Ссылки на файлы pdf/doc/docx:\n")
            # for ref in self.files:
            #     fp.write('\t' + ref + '\n')

            fp.write("Количество не ответивших страниц: " + str(len(self.unanswered_url)) + "\n")

            fp.write("Количество страниц, которые не получилось спарсить: " + str(len(self.unparsed_url)) + "\n")

    def start_crawling(self, start_url: str, page_amount_to_visit: int) -> None:
        self.process_url(URL(start_url))

        while not self.url_queue.empty() and len(self.visited_url) < page_amount_to_visit:
            url = self.url_queue.get()
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.34'}
            
            try:
                resp = requests.get(url.get_full_address(), headers=headers, timeout=10)
            except:
                self.unanswered_url.add(url.get_full_address())
                continue

            if resp.status_code == requests.codes.ok:
                self.visited_url.add(url.domain + url.section)

                try:
                    root = BeautifulSoup(resp.text, features="lxml")
                except:
                    self.unparsed_url.add(url.get_full_address())
                    continue

                self.save_html(str(hash(url.domain + url.section)), str(root))

                for link in root.find_all('a'):
                    href = link.get("href")

                    if href:
                        if re.search(r"mailto:|tel:", href, re.I):
                            continue

                        if href.startswith("//"):
                            href = "https:" + href
                        
                        # if re.search(r"([-\w]+[.])+\w+", url, re.I):
                        #     domain = re.search(r"([-\w]+[.])+\w+", url, re.I).group()
                        # else:
                        #     domain = url.domain
                        
                        # if re.search(r"^https?://", href, re.I):
                        #     protocol = re.search(r"^https?://", url, re.I).group()
                        # else:
                        #     protocol = url.protocol

                        if href.startswith('/'):
                            a = self.process_url(URL(None, url.domain, href, url.protocol))
                        elif not re.search(r"^https?://", href, re.I):
                            href = '/' + href
                            a = self.process_url(URL(None, url.domain, href, url.protocol))
                        elif re.search(r"[a-z]+[.][a-z]+", href, re.I):
                            a = self.process_url(URL(href))
            else:
                self.bad_url.add(url.get_full_address())
            
            if len(self.visited_url) % 100 == 0:
                self.save_stats()