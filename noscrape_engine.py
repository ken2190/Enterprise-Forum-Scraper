from noscrape.noscrape import NoScrape

class Noscraper:
    
    def is_blank(self):
        values = [
            value for value in self.kwargs.values()
            if value
        ]
        return len(values) == 0

    def do_scrape(self):
        NoScrape().run()



def main():
    Noscraper().do_scrape()


if __name__ == '__main__':
    main()
