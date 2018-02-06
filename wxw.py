from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from ebooklib import epub
import uuid
import base64
import argparse

BASE_LINK = 'http://www.wuxiaworld.com/'

def wxw():
    ap = argparse.ArgumentParser()
    ap.add_argument('-u', '--url', default='desolate-era-index')
    ap.add_argument('-b', '--books', nargs='+', default=[1])
    args = ap.parse_args()

    index_link = BASE_LINK + args.url
    index_req = Request(index_link, headers={'User-Agent': 'Mozilla/5.0'})
    index_soup = BeautifulSoup(urlopen(index_req).read(), 'html5lib')

    title = index_soup.find('h1', attrs={'class': 'entry-title'}).get_text().replace(' – Index', '')
    raw_chapter_links = [a['href'] for a in index_soup.select('div[itemprop=articleBody] a[href]')]

    print(raw_chapter_links)
    return

    book = epub.EpubBook()
    book.set_identifier(uuid.uuid4().hex)
    book.set_title(title)
    book.set_language('en')

    # TODO - Generalize for all book / chapter of given title
    base_link = 'http://www.wuxiaworld.com/desolate-era-index/de-book-3-chapter-{}'

    chapters = []

    for i in range(1, 19):
        chapter_link = base_link.format(i)
        req = Request(chapter_link, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req).read()
        soup = BeautifulSoup(page, 'html.parser')

        raw_chapter = soup.find('div', attrs={'itemprop': 'articleBody'})
        parsed_chapter = []

        hr = 0
        for line in raw_chapter:
            if line.name == 'hr':
                hr += 1
            elif hr == 1 and line.name == 'p':
                parsed_chapter.append(line.get_text())

        chapter_title = parsed_chapter[0]
        chapter = epub.EpubHtml(title=chapter_title, file_name='{}.xhtml'.format(chapter_title), lang='en')
        # Chapter Title
        parsed_chapter[0] = '<h1>{}</h1>'.format(parsed_chapter[0])
        chapter.content = '<br /><br />'.join(str(line) for line in parsed_chapter)

        book.add_item(chapter)
        book.toc += (epub.Link(chapter.file_name, chapter.title, chapter.title), )
        chapters.append(chapter)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.spine = ['Nav'] + chapters

    # Not sure exactly what this is doing
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    epub.write_epub('{}.epub'.format(book.title), book, {})

if __name__ == '__main__':
    wxw()
