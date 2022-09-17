import requests
from bs4 import BeautifulSoup
# from bom_tool import Website

# this should be a common object that can be used to interface with report
# object, regardless of the website used to gather data
# each website will have to implement a different define_part method


class FindChips():
    def __init__(self, site_name):
        # Website.__init__(self, site_name)
        self.site_name = site_name
        self.base_url = 'https://www.findchips.com/search/'

    def scrape_site(self, pn, report):
        print("Scraping for " + pn + " on " + self.site_name + ' ...')
        get_part_data(pn, self.get_html(pn), report)
        return

    def get_html(self, pn):
        page = requests.get(self.base_url + pn)
        soup = BeautifulSoup(page.content, 'html.parser')
        return soup


class Part():
    def __init__(self, pn):
        self.pn = pn
        self.distributors = list()
        self.stock = list()
        self.moq = list()
        self.price = list()

    def define_part(self, dist_data):
        if len(dist_data) == 0:
            self.distributors.append('Error: part not found')
            self.stock.append(0)
            self.moq.append(0)
            self.price.append('N/A')
        else:
            for dist in dist_data:
                self.distributors.append(dist[0])
                self.stock.append(dist[1])
                self.moq.append(dist[2])
                self.price.append(dist[3])


def get_part_data(pn, soup, report):
    row_data = list()
    dist_data = list()
    dist_html = soup.find_all('div', class_="distributor-results")
    for distributor in dist_html:
        # isolate table row data ('tr' tag) for each distributor
        table_html = distributor.table.tbody.find_all(class_='row')
        for tr_html in table_html:
            # if table result entry matches part number exactly
            if check_row_pn(tr_html, pn):
                # create entry for table row data
                row_data.append(get_row_data(distributor, tr_html, pn))
        # if the distributor has any stock > 0
        if clean_dist_data(row_data) is not None:
            # filter to one row entry for that distributor and append list
            dist_data.append(clean_dist_data(row_data))
        # empty row_data for next distributor
        del row_data[:]
    # create part object that can be seen by report class
    part = Part(pn)
    # define part attributes per findchips data, indicate if pn is not found
    part.define_part(dist_data)
    report.define_dict(part)
    return


def check_row_pn(tr_html, pn):
    pn_head = tr_html.find(class_='part-name')
    # only load data if pn is an exact match
    if pn_head.a.string.strip() == pn:
        return True
    else:
        return False


# get relevant data from row of findchips table
def get_row_data(distributor, tr_html, pn):
    single_row = list()
    single_row.append(get_distributor(distributor))
    single_row.append(get_stock_data(tr_html))
    moq_data = (get_moq_data(tr_html))
    single_row.append(moq_data[0])      # moq
    single_row.append(moq_data[1])      # moq unit price
    return single_row


def get_distributor(distributor):
    return distributor.get('data-distributor_name')


def get_stock_data(tr_html):
    dumpstr = ''
    # populate current row stock
    stock_head = tr_html.find(class_='td-stock')
    temp_stock = list(stock_head.text.strip())
    if 'on order' in stock_head.text.lower():
        return 0
    # format stock string to delete text and unwanted chars
    for position in range(len(temp_stock)):
        if not temp_stock[position].isdigit():
            temp_stock[position] = ' '
    if dumpstr.join(temp_stock).strip() == '':
        return 0
    else:
        return int(dumpstr.join(temp_stock).strip())


def get_moq_data(tr_html):
    price_table_q = list()
    ascending = False
    qty_head = tr_html.find_all('span', class_='label')

    for item in qty_head:
        price_table_q.append(item.string.strip())

    length = len(price_table_q)
    if length == 0:
        qty = 0
    # check if ascending or descending order to get smallest unit qty
    elif length == 1 or int(price_table_q[0]) < int(price_table_q[1]):
        qty = int(price_table_q[0])
        ascending = True
    else:
        qty = int(price_table_q[-1])
    price = get_price_data(tr_html, length, ascending)
    return qty, price


def get_price_data(tr_html, length, ascending):
    price_table_p = list()

    price_head = tr_html.find_all('span', class_='value')

    for item in price_head:
        price_table_p.append(item.string.strip())
    if length == 0:
        return 'N/A'
    elif length == 1 or ascending:
        return price_table_p[0]
    else:
        return price_table_p[-1]


def clean_dist_data(row_data):
    # row_data[row][1] = qty in stock
    # row_data[roq][2] = min order qty (moq)
    stock = list()
    moq = list()
    for row in row_data:
        stock.append(row[1])
        moq.append(row[2])
    # if no stock, return None
    if max(stock) == 0:
        return
    # if no price / moq data listed
    if max(moq) == 0:
        # get row with greatest stock
        return row_data[stock.index(max(stock))]
    # sort row_data by lowest moq, then highest stock
    sorted_rows = sorted(row_data, key=lambda item: (item[2], -item[1]))
    # get lowest moq with greatest stock that is > 0
    for row in sorted_rows:
        if row[2] > 0 and row[1] > 0:
            return row
    # otherwise, all rows are 0 moq or 0 stock. get greatest stock
    return row_data[stock.index(max(stock))]
