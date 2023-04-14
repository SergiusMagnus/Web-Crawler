from web_crawler import WebCrawler

if __name__ == "__main__":
    spbu_wc = WebCrawler("spbu.ru")
    spbu_wc.start_crawling("https://spbu.ru/", 10)
    spbu_wc.save_stats()

    # msu_wc = WebCrawler("msu.ru")
    # msu_wc.start_crawling("https://www.msu.ru/", 10)
    # msu_wc.save_stats()