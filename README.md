# bib_cleanup

Reads the titles from all entries in a bibtex file and replaces them with the corresponding _dblp_ entries in condesed form.

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
python bib_cleanup.py test.bib out.bib
```



