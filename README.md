# Test Multiple Starter Cycles with Ni-Cad Batteries Following IEEE 1115-2014 Recommendation

Python test procedure of multiple discharge starter cycles on Nickel-Cadmium batteries with the IEEE 1115-2014 algorithm. IEEE 1115-2014 is *Recommended Practice for Sizing Nickel-Cadmium Batteries for Stationary Applications*

Aim of this algorithm is to take an elementary battery block profile, specifically its capacity, its *Kt* capacity rating factor (defined as battery capacity divided by current for a given duration), temperature derating factor, aging factor, maximum depth of discharge, etc (see details in *Usage* section) and find how many battery blocks should be installed to stand a given number of starting cycles

Starting cycles are defined as *periods*. Discharge current is considered constant during each *period*. Calculations are done to assess the required capacity for different so called *sections*. Section *n* is defined as sequence of period from *period 1* to *period n*

For more details about this algorithm see *documentation* folder where a couple of *pdf* files details the process and the rationale. One document refers to IEEE 485 which is a very similar algorithm targeting lead acid batteries instead of Ni-Cad batteries

# What it does

Considering a battery block with a given capacity and a certain number of starter cycles discharging batteries, the evaluation calculates, given a number of *sections*, i.e. steps of starter cycles, how many battery blocks should be needed

This program displays calculation results and optionally intermediate calculations. Those intermediate calculation details are comma separated which eases load those results as a CSV file

# Usage

`python process.py def.json`

with *def.json* being a *json* file with the following example structure:

```json
 {
  "title": "Test...\n details...",
  "nominalCapacity": 100,
  "numberOfSections": 12,
  "verbose": true,
  "deratingFactorOnTemp": 1.0,
  "randomSize": 0.0,
  "designMargin": 1.2,
  "agingFactor": 1.0,
  "finalTolerance": 0.99,
  "csvFileNames":{
   "startingCycles": "starting.csv",
   "ampsByDurationFileName": "amps-per-duration.csv"
   }
 }
```

Where:

- `title` is a header, possibly multiline (with `\n` line breaks)  displayed at the beginning of the result report
- `nominalCapacity` is the elementary battery black capacity in *Ah*
- `numberOfSections` is the number of starter sections to consider to compute the evaluation
- `verbose` if `true` will produce a report with full calculation details, if `false` only result will be displayed
- `deratingFactorOnTemp`, `randomSize`, `designMargin`, `agingFactor` are values used by the IEEE 1115-2014 algorithm
- `finalTolerance` will relax the final size to estimate the number of batteries required (meaning if we are close to a required battery number threshold, threshold will not be crossed). This parameter which range should reasonably be some percent (e.g. between `0.99` and `0.95` for 1 to 5% tolerance) is not defined in the standard, so if no such tolerance is suited, set it at `1.0`
- `csvFileNames` is a place to define file names for *Starting Profile* and battery block *Current per Duration*. See next section for details

## Starting Profile File

This is a CSV (Comma Separated Value) file which defines a starter current profile, composed of cycles. It is composed of three columns with a compulsory header line: Duration*, Current*, *Cycle*. Example:

```csv
Duration,Current,Cycle
00:15:00,5,1
00:10:00,35,1
01:15:00,15,1
00:10:00,60,1
00:10:00,5,1
00:15:00,5,2
00:10:00,35,2
01:15:00,15,2
00:10:00,60,2
00:10:00,5,2
```

In this example, 2 cycles are defined with the same profile of 5 Amps, 35 Amps, 15 Amps, 60 Amps, 5 Amps discharge current for respectively 15, 10, 75, 10, and 10 minutes (given as *hh:mm:ss*, *hh* and *mm* being integers and *ss* a float)

## Current per Duration File

This is a CSV (Comma Separated Value) file which defines battery current for different durations. It is composed of two columns with a compulsory header line: *Duration*, *Current*. Example:

```csv
Duration,Current
00:01:00,189
00:15:00,133
00:30:00,94
01:00:00,58
02:00:00,37
03:00:00,27
04:00:00,22
05:00:00,18
06:00:00,16
07:00:00,14
08:00:00,13
10:00:00,11
12:00:00,9.3
```

In this example, elementary battery block current is defined versus duration, given as *hh:mm:ss*, *hh* and *mm* being integers and *ss* a float

# Result Sample
Test with a 104Ah battery
 defined in "sample/test-with-104Ah-battery.json"
 IEEE 1125-2014 simulation started on 2020/11/09
 Starting data file: "./sample/starting-data.csv"
 Battery current data file: "./sample/amps-per-duration-to-1.05V.csv"

Section 1 skipped

Section 2
|Period|Load|Change|Duration|Remaining|Kt|Temp Derating|Size|
|:---------|:---------|:---------|:---------|:---------|:---------|:---------|:---------|
|1|5.00|5.00|00:15:00.0|00:25:00.0|0.9912|1.19|5.90|
|2|35.00|30.00|00:10:00.0|00:10:00.0|0.6907|1.19|24.66|
Total: 30.56 Ah

Section 3 skipped

Section 4
|Period|Load|Change|Duration|Remaining|Kt|Temp Derating|Size|
|:---------|:---------|:---------|:---------|:---------|:---------|:---------|:---------|
|1|5.00|5.00|00:15:00.0|01:50:00.0|2.6725|1.19|15.90|
|2|35.00|30.00|00:10:00.0|01:35:00.0|2.4542|1.19|87.62|
|3|15.00|-20.00|01:15:00.0|01:25:00.0|2.2870|1.19|-54.43|
|4|60.00|45.00|00:10:00.0|00:10:00.0|0.6907|1.19|36.99|
Total: 86.07 Ah

Result testing 1 cycle
Maximum section size: 86.07 + Random size: 0.00
 = Uncorrected size: 86.07 Ah
Uncorrected size: 86.07 x Design margin: 1.15 x Aging factor: 1.25
 = Size: 123.73 Ah
Number of batteries required: 2 (with a 1.0% tolerance)