<div align="center">
	<img src="https://user-images.githubusercontent.com/10602289/62837228-37fe0f00-bc3b-11e9-90ae-44b798b0511e.png" width="200" height="200">
	<h1>Unravel</h1>
	<p>
		<b>Deanonymize anonymous posters on Piazza Q&A.</b>
	</p>
  <a href="LICENSE" title="License: MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
	<br>
	<br>
	<br>
</div>

## How does it work?
Unravel uses Piazza's API to deduce anonymous posters on Piazza classes. Keeping track of the class statistics, one can deduce the identity by just comparing two class statistics records taken before and after an anonymous post.

Unravel diffs two user statistics data of a given class. Each user in the first statistics gets compared with itself on the second statistics. If a difference is found, Unravel proceeds to diffing posts data of the class to find what was updated by the user.

It then prints out to stdout the change in posts data combined with the user info whose statistics were changed.

```
{'name': 'User 1', 'email': 'eralp@example.com'} {'cid': 24, 'content': '<p>Create a follow up.</p>', 'diff_type': 'followup', 'time': '2019-08-11T16:06:50Z'}
```

## Fields in the result

- `cid`: the CID of the modified post.
- `Content`: Text change made by the anonymous user.
- `time`: Change time.
- `diff_type`: Categorizes the change made by the anonymous user. Can be one of the following:
```python
'post_add' # New post added.
's_answer' # Student answer added.
's_answer_update' # Student answer updated.
'followup' # Created new follow up discussion entry.
'feedback' # Created new reply to a follow up discussion.
```

## Usage
```console
python unravel.py -u piazza_username -p piazza_password -c piazza_class_id
```

- For command-line argument descriptions: `python unravel.py -h`

```console
Piazza Post Deanonymzer.

optional arguments:
  -h, --help   show this help message and exit

Piazza Authentication:
  -u email     Piazza account email
  -p password  Piazza account password
  -c class_id  Class id from piazza.com/class/{class_id}
```

> This is a work in progress, definitely buggy, proof of concept application. Any [feedback](https://github.com/eralpsahin/unravel/issues/new?body=Hi,%0A%0A) is appreciated!
