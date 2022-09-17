# bom-tool, by erfx5361

from findchips import *
import os
import fnmatch
import csv


# A bom object represents dataset used from input csv BOM for future steps
class BoM():
    def __init__(self):
        self.parts = list()
        self.descs = list()
        self.qties = list()
        self.path = str()
        self.fname = str()
        self.contents = list()
        self.start_row = int()      # defines csv row with header data

    # incomplete method. Need to change data form to be in the three lists
    def get_bom(self, report):
        self.get_csv_path()              # define self.path
        self.get_csv_contents()          # define self.contents
        self.get_bom_parts()             # define self.parts
        self.get_bom_qties()             # define self.qties
        # if user wants part descriptions in output report
        if get_user_pref():
            self.get_bom_descs()         # define self.descs
        self.populate_report(report)     # write to report object
        return

    def get_csv_path(self):
        for f in os.listdir(path=os.getcwd()):
            if fnmatch.fnmatch(f, '*.csv'):
                self.path = os.getcwd() + '/' + f
                self.fname = f
        return

    def get_csv_contents(self):
        # Populate list object.
        # Find start of table and populate list with csv contents.
        body = False        # indicates if script has entered body of the table
        match_count = 0
        num_columns = list()

        # get csv file contents
        with open(self.path, newline='') as csvfile:
            contents = csv.reader(csvfile, delimiter=',', quotechar='"')
            for index, row in enumerate(contents):
                self.contents.append(row)
                if body is False:
                    for position, cell in enumerate(reversed(row)):
                        # find perimeter of data in each row
                        if cell.strip('/:\'\\.,"') != '':
                            num_columns.append(len(row) - position)
                            break
                    # look for two consecutive rows with same number of
                    # filled columns to define start row of table
                    if (index != 0 and
                            num_columns[index] == num_columns[index-1]):
                        match_count += 1
                    if match_count == 2:
                        body = True
                        self.start_row = index - match_count
        return

    def get_bom_parts(self):
        pn_aliases = ['pn', 'part num', 'partn', 'p/n']
        pn_index = list()

        for position, column in enumerate(self.contents[self.start_row]):
            column = column.lower()
            # print(column)
            for alias in pn_aliases:
                if alias in column:
                    pn_index.append(position)
        if len(pn_index) == 0:
            print('part number column not found. Add a header with "pn" or'
                  '"part number" in the part column.')
            quit()
        elif len(pn_index) == 1:
            pn_col = pn_index[0]
        else:
            # Try to filter to one, correct, pn column in header
            for position in pn_index:
                # if a header tries to use a "manufacturer" part number, use it
                if ('mfg' or 'manufacturer' or 'mfr' in
                        self.contents[self.start_row][position].lower()):
                    pn_col = position
                    break
                elif (self.contents[self.start_row][position] == "part number"
                      or self.contents[self.start_row][position] == "pn"):
                    pn_col = position
        if pn_col == -1:
            print('it is not obvious which column is supposed to contain part'
                  'numbers, aborting script. Try something with "pn" or'
                  ' "part number" in the table header.')
            quit()
        for row in self.contents[self.start_row + 1:]:
            self.parts.append(row[pn_col])
        return

    def get_bom_qties(self):
        qty_aliases = ['qty', 'quantity', 'qtity', 'qnty']
        qty_col = -1

        for position, column in enumerate(self.contents[self.start_row]):
            column = column.lower()
            for alias in qty_aliases:
                if alias in column:
                    qty_col = position
        if qty_col == -1:
            print('qty column not found, aborting script.')
            exit()
        for row in self.contents[self.start_row + 1:]:
            self.qties.append(row[qty_col])
        return

    def get_bom_descs(self):
        desc_col = -1

        for position, column in enumerate(self.contents[self.start_row]):
            column = column.lower()
            if "desc" in column:
                desc_col = position
        if desc_col == -1:
            print('part description column not found, skipping this field.')
            return
        for row in self.contents[self.start_row + 1:]:
            self.descs.append(row[desc_col])
        return

    def populate_report(self, report):
        for part in self.parts:
            report.add_part(part)
        if len(self.descs) > 0:
            for desc in self.descs:
                report.add_desc(desc)
        for qty in self.qties:
            report.add_qty(qty)
        report.bom_fname = self.fname
        return


# report object is a collection of part objects and report properties
class Report():
    def __init__(self, site):
        self.parts = list()
        self.descs = list()
        self.qties = list()
        self.parts_dict = dict()
        self.site = site
        self.bom_fname = str()
        self.distributors = list()
        self.header = list()
        self.content = list()
        self.footer = list()

    def add_part(self, part):
        self.parts.append(part)
        return

    def add_desc(self, desc):
        self.descs.append(desc)
        return

    def add_qty(self, qty):
        self.qties.append(qty)
        return

    # create dictionary entry for each part
    # accepts part object with attributes: pn, distributors, stock, moq, price
    def define_dict(self, part):
        self.parts_dict[part.pn] = [[part.distributors[0],
                                    part.stock[0],
                                    part.moq[0],
                                    part.price[0]]]
        if len(part.distributors) > 1:
            for index in range(len(part.distributors[1:])):
                self.parts_dict[part.pn].append([part.distributors[index + 1],
                                                 part.stock[index + 1],
                                                 part.moq[index + 1],
                                                 part.price[index + 1]])
        return

    def create_report(self):
        self.get_sorted_distributors()
        self.create_header()
        self.get_content()
        self.create_footer()
        self.write_output_csv()

    def get_sorted_distributors(self):
        distributors = dict()
        # parse all cleaned web data to create a count for each distributor
        # also create tally for number of times they have moq = 1
        for key in self.parts_dict:
            for row in self.parts_dict[key]:
                # check distributor element of list vs list of distributors
                if row[0] not in distributors:
                    distributors[row[0]] = [1]
                    # if stock exists,and moq is 1, increment 2nd list item
                    if row[2] == 1 and row[1] != 0:
                        distributors[row[0]].append(1)
                    # else, create empty count for 2nd list item
                    else:
                        distributors[row[0]].append(0)
                # if distributor already in dictionary
                else:
                    # increment distributor occurence count
                    distributors[row[0]][0] += 1
                    # if stock exists,and moq is 1, increment 2nd list item
                    if row[2] == 1 and row[1] != 0:
                        distributors[row[0]][1] += 1
        # create list of tuples [('Distributor', count, moq==1 count), ...]
        # sorted by most often appearance of valid moq, then distributor count
        temp = sorted(distributors.items(), key=lambda item:
                      (item[1][1], item[1][0]), reverse=True)
        # populate ordered list of distributors from tuples
        for item in temp:
            self.distributors.append(item[0])
        del temp
        del distributors
        return

    def create_header(self):
        self.header.append([self.bom_fname])
        if len(self.descs) == 0:
            header_row2 = ['', '']
            header_row3 = ['pn', 'qty']
        else:
            header_row2 = ['', '', '']
            header_row3 = ['pn', 'desc', 'qty']
        for dist in self.distributors:
            header_row2.append(dist)
            header_row2.append('')
            header_row2.append('')
            header_row3.append('stock')
            header_row3.append('MOQ')
            header_row3.append('MOQ price')
        self.header.append(header_row2)
        self.header.append(header_row3)
        return

    def get_content(self):
        dist_found = False
        for pos in range(len(self.parts)):
            if len(self.descs) != 0:
                content_row = [self.parts[pos],
                               self.descs[pos], self.qties[pos]]
            else:
                content_row = [self.parts[pos], self.qties[pos]]
            # loop through order of distributor list, append blanks as needed
            for dist in self.distributors:
                for row in self.parts_dict[self.parts[pos]]:
                    if row[0] == dist:
                        dist_found = True
                        for element in row[1:]:
                            content_row.append(element)
                if not dist_found:
                    for num in range(3):
                        content_row.append('')
                dist_found = False
            self.content.append(content_row.copy())
            del content_row[:]
        return

    def create_footer(self):
        self.footer.append('')
        self.footer.append(['Report for ' + self.bom_fname +
                            ' from ' + self.site])

    def write_output_csv(self):
        # make directory for result csv
        # write results to csv
        fname = os.getcwd() + '/output.csv'
        with open(fname, 'a', newline='') as csvfile:
            report_data = csv.writer(csvfile, delimiter=',', quotechar='"')
            for row in self.header:
                report_data.writerow(row)
            for row in self.content:
                report_data.writerow(row)
            for row in self.footer:
                report_data.writerow(row)
        return


def user_ready():
    ready = input('A target bill of materials .csv file should be the only'
                  ' csv file in this directory.\nContinue? Y/N: ')
    if ready.lower().startswith('y'):
        user_ready = True
    elif ready.lower().startswith('n'):
        user_ready = False
    else:
        print('User input was not understood.')
        user_ready = False
    return user_ready


def get_user_pref():
    report_desc = input('Do you want to include part descriptions in '
                        'output csv report? Y/N: ')
    if report_desc.lower().startswith('y'):
        user_desc = True
    elif report_desc.lower().startswith('n'):
        user_desc = False
    else:
        print('User input was not understood.'
              ' Defaulted to no. Try, say... "y" or "n".')
        report_desc = input('Last chance, Y/N?: ')
        if report_desc.lower().startswith('y'):
            user_desc = True
        else:
            user_desc = False
    return user_desc


def main():
    if not user_ready():
        exit()

    bom = BoM()
    fc = FindChips('findchips.com')
    rep = Report(fc.site_name)
    bom.get_bom(rep)
    for part in rep.parts:
        fc.scrape_site(part, rep)
    rep.create_report()


if __name__ == "__main__":
    main()
