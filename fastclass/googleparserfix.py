# Fix for changes in Google API Feb/March 2020
# Proposed fix by here: https://github.com/hellock/icrawler/issues/65#issuecomment-614135227

from bs4 import BeautifulSoup
from icrawler import Parser
import re


class GoogleParser(Parser):
    def parse(self, response):
        soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "lxml")
        # image_divs = soup.find_all('script')
        image_divs = soup.find_all(name="script")
        for div in image_divs:
            # txt = div.text
            txt = str(div)
            # if not txt.startswith('AF_initDataCallback'):
            if "AF_initDataCallback" not in txt:
                continue
            if "ds:0" in txt or "ds:1" not in txt:
                continue
            # txt = re.sub(r"^AF_initDataCallback\({.*key: 'ds:(\d)'.+data:function\(\){return (.+)}}\);?$",
            #             "\\2", txt, 0, re.DOTALL)
            # meta = json.loads(txt)
            # data = meta[31][0][12][2]
            # uris = [img[1][3][0] for img in data if img[0] == 1]

            uris = re.findall(r"http.*?\.(?:jpg|png|bmp)", txt)
            return [{"file_url": uri} for uri in uris]
