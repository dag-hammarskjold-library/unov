# unov

## Objectve
Create complete import packages for UNOV's Titanium export, previously hosted on DSpace. 

## Context
Document files were exported from DSpace and pushed to S3, where they were made available for script-based processing. Metadata was collected and refined through other processes, then distilled into unov_metadata.csv. Additional minor edits were necessary to correct the data for package generation. All of the supplementary data needed to run the main script is here.

## Execution
The main script, unov_marcup.py, creates new DLS records for documents not already in DLS, and update existing records with new data/files found in S3. 

### Setup
It's best to run this from a python virtual environment running python 3. Example setup:

`$ virtualenv -p python3 venv`

Then to enter the virtualenv:

`$ source venv/bin/activate`

### Run the script
Enter your virtualenv as above and then:
```
(venv)$ git clone https://github.com/dag-hammarskjold-library/unov/
(venv)$ cd unov
(venv)[unov]$ pip install -r requirements.txt
(venv)[unov]$ python unov_marcup.py
```
leverages a650.dat, a651.dat, file_map.dat, and symbol_map.dat to populate new.xml and update.xml

**NOTE** The pymarc library in use for this package has been altered from the base pymarc package. DO NOT install the pymarc library from its main repository, or you will end up with wrongly-encoded files. This requirement is in place until the upstream repo incorporates the needed changes.

To determine whether records are new vs update, the program makes use of symbol_map.dat. New records are those for which no symbol match occurs. 

The other .dat files are additional lookups. file_map.dat is the output of mapper.py and provides a docsymbol-based lookup of S3 URLs for inclusion in FFT tags. a650.dat and a651.dat are for authorities lookup.

## To do
While this is a one-off script, it is apparent that we could use a set of standard tools to facilitate analysis of existing DLS metadata. The suggestions below are those which should be incorporated into a set of standalone libraries.
* It would be helpful if we could programmatically update symbol_map.dat. 
* A comprehensive authorities map to supplant a650.dat and a651.dat is also desirable.

I can think of no immediate way to adequately abstract the requirements satisfied by mapper.py and its output, file_map.dat, but as long as we continue using S3 to collect and hold files and file packages, we should consider a standard mapping tool.
