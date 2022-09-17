# bom-tool
Designed to reduce labor around part shortages with small-scale agile production in mind. Reads electrical BOM, produces csv report of component availability data. Uses findchips.com to get inventory data.

## Instructions
 - Drop bom_tool.py and findchips.py into a directory with your BOM saved as a .csv file
 - BOM should be only .csv file in directory
 - Run bom_tool.py
 - Choose whether part descriptions should be included in report
 - An report named output.csv will be generated in that directory

## BOM Assumptions
 - Any generic csv file of a typical parts list format should work for this tool
 - The csv file should have a header, but it need not be the first row
 - The tool identifies a part number column, looking for "pn" "part num" "partn" "p/n" in header
   - If multiple columns match, it looks for "mfg" or "manufacturer"
 - The tool identifies quantity and description columns, looking for "qty", "quantity", "qtity", "qnty", or "desc" in header
 - The tool looks for two rows of the same number of columns to define where the BOM data starts
 
 ## Report Behavior
  - Report transfers part numbers and quantities from BOM to report (and optionally descriptions)
  - Report displays reported stock, minimum order quantity (moq), and price for moq for each distributor
  - Distributors are sorted left to right, by number of times they offer an moq of 1 across BOM, secondarily by number of appearances
  - Report only supports exact matches for part numbers, part numbers that are not found will still be listed, but with no inventory data

 ## Potential Areas of Improvement
  - Allow for part number wildcards to provide flexibility in result reporting for "don't care" configurations such as packaging type
  - Add capability for other distributor aggregation sites if there is a need

 ## Donate
  - If you found this tool helpful, consider donating to the [python software foundation](https://www.python.org/psf/donations/) or the [EFF](https://supporters.eff.org/donate/join-eff-4)
