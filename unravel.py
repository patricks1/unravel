#!venv/bin/python
'''Unravel, Piazza Deanonymizer'''
import argparse
import time

from piazza_api import Piazza
from tinydb import TinyDB
from jsondiff import diff


def get_statistics(email, password, class_id):
    """Logins to Piazza and retrieves the statistics of a class.

    Args:
        email: Piazza username.
        password: Piazza password.
        class_id: Class ID on Piazza.

    Returns:
        A JSON formatted class statistics.

    Raises:
        piazza_api.exceptions.AuthenticationError:
            If authentication fails.
    """
    piazza = Piazza()
    piazza.user_login(email, password)
    return piazza.network(class_id).get_statistics()


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


def main():
    '''Get the cli args and start tracking.'''
    args = parse_arguments()
    # TODO: Update the sleep time
    while True:
        track(args)
        time.sleep(5)


def track(args):
    """Tracks the statistics of the Piazza class and checks the diff
    of the users in two records to find the poster.

    Args:
        args: {
            email: Piazza username.
            password: Piazza password.
            class_id: Class ID on Piazza.
        }
    """

    stats = get_statistics(args.email, args.password, args.class_id)
    stats = {'users': stats['users'],
             'total': stats['total'], 'top': stats['top_users']}

    # Create/load tinydb for the class
    tinydb = TinyDB(f'{args.class_id}.json', default_table="class_stats")
    # Insert the new stats record to the database
    tinydb.insert(stats)
    # Find the difference between this stats and the previous one
    if len(tinydb.all()) == 2:
        find_diff(args.class_id)
        tinydb.purge()
        tinydb.insert(stats)
    elif len(tinydb.all()) < 2:
        print("No previous record. Program will start comparing with the next record.")
    else:
        # There should not be more than 2 records in the database anytime.
        # Delete the database and start over.
        print("Number of recors are greater than 2. Removing all but the most recent one.")
        tinydb.purge()
        tinydb.insert(stats)


def sanitize_user(user):
    """Sanitizes the given json by removing the following keys:
        lti_ids, user_id, days, views

    Args:
        user: Json object for user.

    Returns:
        A sanitized JSON user object.

    Raises:
        KeyError: If any of the mentioned keys does not exist.
    """
    del user['lti_ids'], user['user_id'], user['days'], user['views']
    return user


def find_diff(class_id):
    """Compares the previous and current class statistics.

    Args:
        class_id: Class ID on Piazza.

    Searches for difference in a user between two statistics records
    in the tinydb database, prints the users with difference.
    """
    tinydb = TinyDB(f'{class_id}.json', default_table="class_stats")

    total_info = tinydb.all()[0].get('total')
    print(f'Total in the class: {total_info}')

    prev = tinydb.all()[0].get('users')
    curr = tinydb.all()[1].get('users')

    # Find a difference in a user data between two statistics records
    found = False
    for index, prev_user in enumerate(prev):
        prev_user = sanitize_user(prev_user)
        curr[index] = sanitize_user(curr[index])
        if diff(prev_user, curr[index], syntax='explicit') != {}:
            print(curr[index])
            found = True

    if not found:
        print("There was no difference")


if __name__ == '__main__':
    main()
