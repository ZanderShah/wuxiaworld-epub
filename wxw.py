from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from ebooklib import epub
import uuid
import base64
import argparse
import re
import time

BASE_LINK = 'http://www.wuxiaworld.com/'

def wxw():
    ap = argparse.ArgumentParser()
    ap.add_argument('-u', '--url', default='desolate-era-index')
    ap.add_argument('-b', '--books', nargs='+', default=None)
    args = ap.parse_args()

    index_link = BASE_LINK + args.url
    index_req = Request(index_link, headers={'User-Agent': 'Mozilla/5.0'})
    index_soup = BeautifulSoup(urlopen(index_req).read(), 'html5lib')

    series_title = re.search(r'([^:–()])*\w', index_soup.find('h1', attrs={'class': 'entry-title'}).get_text()).group()

    raw_chapter_links = a['href'] for a in index_soup.select('div[itemprop=articleBody] a[href]')
    books = {}
    chapters = {}

    book_titles = index_soup.find('div', attrs={'itemprop': 'articleBody'}).find_all('strong')
    for book in book_titles:
        book_number = re.search(r'^\w*\s\d+', book.get_text())
        if book_number is None:
            continue
        book_number = re.search(r'\d+', book_number.group()).group()
        if args.books is not None and book_number not in args.books:
            continue
        books[book_number] = epub.EpubBook()
        books[book_number].set_title('{} – {}'.format(series_title, book.get_text()))
        books[book_number].set_identifier(uuid.uuid4().hex)
        books[book_number].set_language('en')
        chapters[book_number] = []

    for raw_chapter_link in raw_chapter_links:
        info = re.search(r'\w*-\d+', raw_chapter_link)
        if info is None:
            continue
        book_number = re.search(r'\d+', info.group()).group()
        if book_number not in books:
            continue

        chapter_req = Request(raw_chapter_link, headers={'User-Agent': 'Mozilla/5.0'})
        chapter_soup = BeautifulSoup(urlopen(chapter_req).read(), 'html5lib')
        raw_chapter = chapter_soup.find('div', attrs={'itemprop': 'articleBody'})

        parsed_chapter = []

        hr = 0
        for line in raw_chapter:
            if line.name == 'hr':
                hr += 1
            elif hr == 1 and line.name == 'p':
                parsed_chapter.append(line.get_text())

        chapter_title = re.search(r'\w([^–:])*$', parsed_chapter[0]).group()
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name='{}.xhtml'.format(uuid.uuid4().hex),
            lang='en'
        )
        # Chapter Title
        parsed_chapter[0] = '<h1>{}</h1>'.format(chapter_title)
        chapter.content = '<br /><br />'.join(str(line) for line in parsed_chapter)

        books[book_number].add_item(chapter)
        books[book_number].toc += (epub.Link(chapter.file_name, chapter.title, uuid.uuid4().hex), )
        chapters[book_number].append(chapter)
        time.sleep(1)
        print('Finished parsing', raw_chapter_link)

    for book_number, book in books.items():
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['Nav'] + chapters[book_number]

        # Not sure exactly what this is doing
        style = 'BODY {color: white;}'
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)

        epub.write_epub('{}.epub'.format(''.join(c for c in book.title if c.isalnum())), book, {})

if __name__ == '__main__':
    wxw()
