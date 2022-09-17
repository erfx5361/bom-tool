# bom-tool
Reads electrical BOM, produces csv report of component availability data. Currently only uses findchips.com to get inventory data.

## Instructions
 - Drop bom_tool.py and findchips.py into a directory with your BOM saved as a .csv file
 - BOM should be only .csv file in directory
 - Run bom_tool.py
 - Choose whether part descriptions should be included in report
 - An report named output.csv will be generated in that directory

## BOM Assumptions
 - Any generic csv file of a typical parts list format should work for this tool.
 - The csv file should have a header, but it need not be the first row.
 - The tool identifies a part number column, looking for "pn" "part num" "partn" "p/n" in header
   - If multiple columns match, it looks for "mfg" or "manufacturer"
 - The tool identifies quantity and description columns, looking for "qty", "quantity", "qtity", "qnty", or "desc" in header
 - The tool looks for two rows of the same # of columns to define where the BOM data starts.
 
 ## Report Behavior
  - Report transfers part numbers and quantities from BOM to report (and optionally descriptions)
  - Report displays reported stock, minimum order quantity (moq), and price for moq for each distributor
  - Distributors are sorted left to right, by number of times they offer an moq of 1 across BOM, secondarily by number of appearances
