from course_lookup import *


course_strings = [
    'CS 2110',
    'CS 1110',
    'CS 2800',
    'CS 3700',
    'MATH 2210',
    'CS 1380',
    'AEM 3050',
]


data = get_course_details(base_str_to_course('CS 2110'))

print(('\n').join(data.keys()))