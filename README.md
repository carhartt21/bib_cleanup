# bib_cleanup

Reads all entries in a bibtex file and uses the titles to replace them with the corresponding _dblp_ entries in condensed form.

## Usage
```
pip install -r requirements.txt

python bib_cleanup.py --input <input_file> [--output <output_file> --failed <file for failed entries>]
```

If no output file is provided the input file will be overwritten. 
The second output file can be used to store entries where the dblp lookup failed 
Otherwise these entries are written to the end of the output file.

## Example
Run
```
python bib_cleanup.py --input test.bib --output out.bib
```



