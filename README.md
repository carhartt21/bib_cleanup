# bib_cleanup

Reads all entries in a bibtex file and uses the titles to replace them with the corresponding [dblp](https://dblp.org/) entries in condensed form. 
Alternatively the bib file can be created from a txt file where each line contains the publication title.

## Usage
### Install requirements
```
pip install -r requirements.txt
```

### Bib cleanup
```
python bib_cleanup.py <input_file> [--output <output_file> --failed <file for failed entries> --long <bool>]
```
If no `--output` is provided the input file will be overwritten. 
The second output `--failed` file can be used to store entries where the dblp lookup failed.
Otherwise these entries are written to the end of the output file.
By default the condensed version of the _dblp_ entry is used. 
With `--long True` the output can be changed to the longer standard version.  

### Txt lookup
```
python txt_lookup.py <input_file> [--output <output_file> --failed <file for failed entries> --long <bool>]
``` 
Uses the same options as 'bib_cleanup'.

## Example
```
python bib_cleanup.py --input test.bib --output out.bib --failed failed.bib
```
```
python txt_lookup.py --input test.txt --output out.bib --failed failed.txt --long True
```



