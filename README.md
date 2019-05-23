# Unravel
> Unravel deanonymizes anonymous posters on Piazza.

Unravel uses Piazza's API to deduce anonymous posters on Piazza classes. Keeping track of the class statistics, one can deduce the identity by just comparing two class statistics records taken before and after an anonymous post.

Currently Unravel gets statistics every 5 seconds. It compares each user statistics with itself in two statistics records and prints students with difference between the records.



## Usage
```console
python unravel.py -u piazza_username -p piazza_password -c piazza_class_id
```

- For command-line argument descriptions: `python unravel.py -h`

> This application is a work in progress. Please give feedback!
