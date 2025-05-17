import re
import sys
import datetime
import asyncio
import aiohttp as aiohttp
import pandas as pd
from bs4 import BeautifulSoup

from src import utils


logger = utils.create_logger("outputs")


class BooksScraper:
    def __init__(self):
        logger.info("Firing up...")
        self.base = "http://books.toscrape.com"
        logger.info(f"Base: {self.base}")
        self.catalogue = self.base + "/catalogue"
        logger.info(f"Catalogue: {self.catalogue}")
        self.nav = self.catalogue + "/category/books_1"
        logger.info(f"Nav: {self.nav}")
        self.params = {}
        self.book_links = []
        self.data = []

    async def fetch(self, url):
        logger.info(f"Fetching {url}...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
            
                return await resp.text()

    async def make_soup(self, url):
        logger.info("Making soup...")
        content = await self.fetch(url)
        doc = BeautifulSoup(content, 'html.parser')

        return doc

    async def find_next(self, doc):
        link_el = doc.select_one('li.next a')
        return link_el['href']

    async def find_from_and_to(self, doc):
        ix_pager = doc.select_one('ul.pager li.current').text.strip()

        from_match = re.findall(r"(?<=Page )\d{1,2}", ix_pager)
        self.params['from'] = int(from_match[0])
        to_match = re.findall(r"(?<=of )\d{1,2}", ix_pager)
        self.params['to'] = int(to_match[0])

    async def clean_link(self, link):
        clink = re.sub(r"(\.\./){0,3}", "", link)

        return clink

    async def extract_links_and_titles(self, doc):
        els = doc.select('article.product_pod h3 a')
        links_and_titles = [
            await self.clean_link(el['href']) for el in els
        ]
        
        self.book_links += links_and_titles

    async def process_book(self, doc):
        title = doc.select_one('div.product_main h1').text.strip()
        price = doc.select_one('div.product_main p.price_color').text.strip()
        desc_title = doc.select_one("div#product_description")
        descn = desc_title.find_all_next("p")[0].text.strip()

        self.data.append((title, price, descn))

    async def main(self):
        logger.info("Checking if requested a specific number of books...")
        if len(sys.argv) >= 2:
            books_to = int(sys.argv[1])
            logger.info(f"Will write a csv with {books_to} books.")
        else:
            books_to = -1
            logger.info("Scraping all available books.")

        logger.info("Going through the catalogue...")
        logger.info("Starting on index page...")
        doc = await self.make_soup(self.nav + "/index.html")
        await self.find_from_and_to(doc)
        await self.extract_links_and_titles(doc)
        next_link = await self.find_next(doc)

        last = self.params['to']+1
        for page in range(self.params['from']+1, last):
            logger.info(f"On page {page}")
            doc = await self.make_soup(self.nav + "/" + next_link)
            await self.extract_links_and_titles(doc)
            if page != last-1:
                next_link = await self.find_next(doc)

        logger.info("Processing books...")
        for href in self.book_links[0:books_to]:
            logger.info(f"Current book: {href}")
            doc = await self.make_soup(self.catalogue + "/" + href)
            await self.process_book(doc)

        df = pd.DataFrame(
            self.data,
            columns = ["title", "price", "description"]
        )
        df["href"] = self.book_links[0:books_to]
        timestamp = str(datetime.datetime.now().isoformat())
        df.to_csv(f"outputs/scrape_{timestamp}.csv")


if __name__ == "__main__":
    scraper = BooksScraper()
    asyncio.run(scraper.main())
