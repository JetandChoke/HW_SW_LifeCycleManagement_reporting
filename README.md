# HW_SW_LifeCycleManagement_reporting
Parse the equipment install base DB, fetch HW/SW lifecycle info and create a report

Create monthly LCM reports in one click!

**Requirements:**

1. Install base DB report
2. HW LCM report as a template and release date info for HW components
3. Release info csv with release dates for SW versions

Produces

result_hw.csv with HW lifecycle info
result_hw_ib.csv with HW IB numbers
result_sw.csv with SW lifecycle info and IB numbers per HW/SW combinations


Pulls data from: https://www.arista.com/custom_data/bug-alert/alertBaseDownloadApi.php
