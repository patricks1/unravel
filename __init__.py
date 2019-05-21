'''Unravel, Piazza Deanonymizer'''
import pprint
from piazza_api import Piazza


def get_statistics(username, password, course_id):
    """Logins to Piazza and retrieves the statistics of a course.

    Args:
        username: Piazza username.
        password: Piazza password.
        course_id: Course ID on Piazza.
    Returns:
        A JSON formatted course statistics.
    """
    piazza = Piazza()
    piazza.user_login(username, password)
    course = piazza.network(course_id)
    return course.get_statistics()


if __name__ == "__main__":
    pass
