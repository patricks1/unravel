"""Unravel, Piazza Deanonymizer"""
import argparse
import time
import json

from piazza_api import Piazza
from tinydb import TinyDB
from jsondiff import diff
#from progressbar import ProgressBar

def get_change_content(children, when):
    """Checks every childrens history recursively to find the content
    of the change.

    Args:
        children: children array of the post dict.
        when: Time of change log dict.

    Returns:
        Content of the change in HTML format.
    """

    for child in children:
        if child.get('updated') == when:
            return child.get('subject')
        if child.get('history') is not None:  # an answer
            for hist in child.get('history'):
                if hist.get('created') == when:
                    return hist.get('content')
        elif len(child.get('children')) >= 1:
            found = get_change_content(child['children'], when)
            if found is not None:
                return found
    return None


def retrieve_posts(piazza_class):
    """Retrieve posts of the class.

    Args:
        piazza_class: Piazza class instance.

    Returns:
        Dict of every post in the class.
    """

    feed = piazza_class.iter_all_posts()
    posts = {}
    print('Diff found.')
    for index,post in enumerate(feed):
        print('Retrieving post {0:d}.'.format(index+1), end='\r')
        time.sleep(1)
        posts[index] = post
    return posts


def sanitize_user(user):
    """Sanitizes the given dict by removing the following keys:
        lti_ids, user_id, days, views
        These fields pollute the diff result unnecessarily.

    Args:
        user: User dict.

    Returns:
        A sanitized user dict.

    Raises:
        KeyError: If any of the mentioned keys does not exist.
    """
    del user['lti_ids'], user['user_id'], user['days'], user['views']
    return user


def parse_arguments():
    """Parses command-line arguments.

    Returns:
        {
            email: Piazza username.
            password: Piazza password.
            class_id: Class ID on Piazza.
        }

    Raises:
        ArgumentError: If any of the arguments is missing.
    """

    parser = argparse.ArgumentParser(description='Piazza Post Deanonymzer.')
    group = parser.add_argument_group('Piazza Authentication')
    group.add_argument('-u', metavar='email', type=str,
                       help='Piazza account email', dest="email")
    group.add_argument('-p', metavar='password', type=str,
                       help='Piazza account password', dest="password")
    group.add_argument('-c', metavar='class_id', type=str,
                       help='Class id from piazza.com/class/{class_id}', dest="class_id")
    args = parser.parse_args()
    if not (args.email and args.password and args.class_id):
        parser.error("the following arguments are required: -u -p -c.")

    return args


def track(piazza, class_id, userdb, postdb):
    """Tracks the user statistics of the Piazza class
    and the posts data of the class to find the anonymous poster and the post.

    Args:
        piazza: Logged in Piazza instance.
        class_id: Class ID on Piazza for tracking.
        userdb: User TinyDB database.
        postdb: Post TinyDB database.
    """

    piazza_class = piazza.network(class_id)

    if not postdb.all():
        postdb.insert(retrieve_posts(piazza_class))

    # Insert the new stats record to the database
    stats = piazza_class.get_statistics()
    stats = {'users': stats['users'],
             'total': stats['total'], 'top': stats['top_users']}
    userdb.insert(stats)

    # Find the difference between this stats and the previous one
    if len(userdb.all()) == 2:
        find_diffs(piazza_class, userdb, postdb)
        userdb.purge()
        userdb.insert(stats)
    elif len(userdb.all()) < 2:
        print("No previous record. Program will start comparing with the next record.")
    else:
        print("Number of records are greater than 2. Removing all but the most recent one.")
        userdb.purge()
        postdb.purge()
        userdb.insert(stats)


def find_post_diff(postdb):
    """Compares the previous and current posts data.

    Args:
        postdb: Post TinyDB database.

    Returns:
        The diff dict of an updated posts change log.
        {
            cid: Post CID on Piazza
            content: Updated text
            diff_type: Change type on the post
            time: Date of change
        }
    """

    prev = postdb.all()[0]
    curr = postdb.all()[1]

    if len(prev) > len(curr):  # New post
        recent = prev['0']['history'][-1]
        subject = recent['subject']
        when = recent['created']
        return {
            "cid": prev['0']['nr'],
            "content": subject,
            "diff_type": "post_delete",
            "time": when
        }
    if len(prev) < len(curr):
        recent = curr['0']['history'][-1]
        subject = recent['subject']
        when = recent['created']
        return {
            "cid": curr['0']['nr'],
            "content": subject,
            "diff_type": "post_add",
            "time": when
        }
    for post in prev:
        # Find a difference in a post change log
        difference = diff(prev[post]['change_log'], curr[post]
                          ['change_log'], syntax='explicit', dump=True)
        difference = json.loads(difference)  # Convert to json
        if difference != {}:
            try:
                diff_type = difference['$insert'][0][1]['type']
                when = difference['$insert'][0][1]['when']
            except KeyError:
                print('Key Error: {}'.format(difference))
            change = get_change_content(curr[post]['children'], when)
            return {
                "cid": curr[post]['nr'],
                "content": change,
                "diff_type": diff_type,
                "time": when
            }
    return None


def find_diffs(piazza_class, userdb, postdb):
    """Compares the previous and current class statistics.
    Diffs every user dict in previous and the current record.

    Args:
        userdb: User TinyDB database.
        postdb: Post TinyDB database.
    """

    prev = userdb.all()[0].get('users')
    curr = userdb.all()[1].get('users')

    # Find a difference in a user data between two statistics records
    user = None

    for index, prev_user in enumerate(prev):
        prev_user = sanitize_user(prev_user)
        curr[index] = sanitize_user(curr[index])
        difference = diff(prev_user, curr[index], syntax='explicit')
        if difference != {}:
            user = {"name": curr[index]['name'], "email": curr[index]['email']}

    if user is not None:
        posts = retrieve_posts(piazza_class)
        postdb.insert(posts)
        post_diff = find_post_diff(postdb)
        postdb.purge()
        postdb.insert(posts)
        print(user, post_diff)


def main():
    """Get the cli args and start tracking."""
    args = parse_arguments()
    piazza = Piazza()
    piazza.user_login(args.email, args.password)
    # Create/load tinydb for the users and posts
    userdb = TinyDB('{}.json'.format(args.class_id), default_table="users")
    postdb = TinyDB('{}.json'.format(args.class_id), default_table="posts")
    while True:
        track(piazza, args.class_id, userdb, postdb)
        time.sleep(3)


if __name__ == '__main__':
    main()
