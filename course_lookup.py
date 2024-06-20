import bs4, requests, json, re, itertools, string, networkx as nx
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from urllib.request import urlopen
from time import sleep

from course import *
from typing import *

#######################################################################################################################################################
#                                                                                                                                                     #
#                                                                      CONSTANTS                                                                      #
#                                                                                                                                                     #
#                               Constant variables to be used for web scraping and data extraction using Beautiful Soup                               #
#                                                                                                                                                     #
#######################################################################################################################################################

COURSE_SEARCH_2024_2025 = 'https://courses.cornell.edu/content.php?filter%5B27%5D=-1&filter%5B29%5D={code_or_number}&filter%5Bcourse_type%5D={subject_code}&filter%5Bkeyword%5D=&filter%5B32%5D=1&filter%5Bcpage%5D=1&cur_cat_oid=60&expand=&navoid=26201&search_database=Filter#acalog_template_course_filter'
COURSES_HOME_2024_2025  = 'https://courses.cornell.edu/content.php?catoid=60&navoid=26201'
COURSE_DETAILS_BASE     = 'https://courses.cornell.edu/'

COURSE_RE = r'[A-Z]+ [1-4]{1}[0-9]{3}'

COURSE_FOLDER = os.getcwd() + os.sep + 'course_jsons' + os.sep + '{subject}'
COURSE_FILE_PATH = os.getcwd() + os.sep + 'course_jsons' + os.sep + '{subject}' + os.sep + '{subject}_{number}.json'

COURSE_DESCRIPTION = '''{name}

[Crosslisted] {crosslisted}
[Distributions] {distributions}
[Seasons Offered] {seasons_offered}
[Credits] {credits}

{body}
'''

ABBREV_REGEX = r'\b((?:[a-zA-Z]\.){2,})'

#######################################################################################################################################################
#                                                                                                                                                     #
#                                                                       METHODS                                                                       #
#                                                                                                                                                     #
#######################################################################################################################################################

def get_subject_codes():
    soup = BeautifulSoup(urlopen(COURSES_HOME_2024_2025).read(), 'html.parser')
    candidates = soup.find_all('option')
    candidates = list(filter(lambda x: re.match('(\d){5}', x.get('value')) and '—' in x.text, candidates))

    return {
        candidate.text.split('—')[0].strip() : {
            'link' : COURSE_SEARCH_2024_2025,
            'code' : int(candidate.get('value')),
            'name' : candidate.text.split('—')[1].strip()
        } for candidate in candidates
    }

SUBJECTS = get_subject_codes()

def base_str_to_course(base_str : str):
    """Retrieves course data from provided base str
    
    Args:
        base_str (str): a str representing a Course object, in the format "{SUBJECT} {CODE}"
    
    Returns:
        course (Course): returns a Course object, queried with the provided SUBJECT and CODE
    """
    subject, number = tuple(base_str.split(' '))
    return Course(
        subject, 
        int(number), 
        ''
        # get_course_details(Course(subject, int(number), ''))['name']
    )

def parse_course_data(
    course_data: bs4.BeautifulSoup,
    course_subject: str,
    course_number: int
):
    print(f"Crawling data for course {course_subject} {str(course_number)}")
    course_details = list(course_data.find_all('td', {'class' : 'block_content'})[0])
    course_details = list(filter(lambda x: type(x) == bs4.element.Tag and x.name == 'p', course_details))[0]

    bs_tags = list(course_details)
    br_tag_indices = [0] + [i for i, tag in enumerate(bs_tags) if tag.name == 'br']
    br_tag_splits = [list(filter(lambda tag: tag.get_text().strip() != '', bs_tags[br_tag_indices[i] : br_tag_indices[i + 1]])) for i in range(len(br_tag_indices) - 1)]

    joined_splits = [re.sub(r'[\s]+', ' ', ("").join([tag.get_text() for tag in split])) for split in br_tag_splits]
    joined_splits = list(filter(lambda x: x.strip() != '', joined_splits))
    raw = ('\n\n').join(joined_splits)
    
    course_name = None
    crosslisted = list()
    if '(crosslisted)' in joined_splits[0]:
        course_name, crosslisted = tuple([text.strip() for text in joined_splits[0].split('(crosslisted)')])
        crosslisted = re.findall(COURSE_RE, crosslisted, re.IGNORECASE)
    else:
        course_name = joined_splits[0]

    course_info = list(filter(lambda x: x.strip() != '', joined_splits[1].split('.')))
    distributions = re.findall(r'[A-Z]+-[A-Z]+', course_info[0], re.IGNORECASE)
    seasons = [text.capitalize() for text in re.findall(r'\b(Spring|Summer|Fall|Winter)\b', course_info[0], re.IGNORECASE)]
    grading = course_info[-1]
    credits = int(re.search(r'(\d+)\s+credits', ('.').join(course_info[1:-1])).group(1))

    print("Distributions : " + str(distributions))
    print("Seasons : " + str(seasons))
    print("Grading : " + grading)
    print("Credits : " + str(credits))    

    joined_splits = joined_splits[2:]

    prereq_str = ''
    prerequisites = list()
    
    forbidden_str = ''
    forbidden_overlaps = set([f'{course_subject} {str(course_number)}'])

    remaining_splits = list()

    for joined_split in joined_splits:
        if len(re.findall(r'Prerequisite', joined_split, re.IGNORECASE | re.DOTALL)) > 0:
            prereq_str = joined_split
            # First replace all abbreviations such that periods corresponding to abbreviations aren't processed
            abbrevs = re.findall(ABBREV_REGEX, prereq_str)
            prereq_str = re.sub(ABBREV_REGEX, "ABBREV_REGEX", prereq_str)

            # Parse the first sentence for prerequisites
            first_sentence = re.findall(r'Prerequisite.*?\.', prereq_str, re.IGNORECASE | re.DOTALL)[0]
            prerequisites = re.findall(COURSE_RE, first_sentence)

            # Return the abbreviations to where they belong
            while len(abbrevs) > 0:
                prereq_str = re.sub(pattern = 'ABBREV_REGEX', repl = abbrevs.pop(0), string = prereq_str, count = 1)

        elif len(re.findall(r'Forbidden Overlap', joined_split, re.IGNORECASE | re.DOTALL)) > 0:
            forbidden_str = joined_split
            # First replace all abbreviations such that periods corresponding to abbreviations aren't processed
            abbrevs = re.findall(ABBREV_REGEX, forbidden_str)
            forbidden_str = re.sub(ABBREV_REGEX, "ABBREV_REGEX", forbidden_str)

            # Parse the first sentence for prerequisites
            first_sentence = re.findall(r'Forbidden Overlap.*?\.', forbidden_str, re.IGNORECASE | re.DOTALL)[0]
            forbidden_overlaps.update(re.findall(COURSE_RE, first_sentence, re.IGNORECASE | re.DOTALL))

            # Return the abbreviations to where they belong
            while len(abbrevs) > 0:
                forbidden_str = re.sub(pattern = 'ABBREV_REGEX', repl = abbrevs.pop(0), string = forbidden_str, count = 1)

        else:
            remaining_splits.append(joined_split)

    prerequisites = [course for course in prerequisites if course not in forbidden_overlaps]

    print("Prerequisites : " + str(prerequisites))
    print("Prerequisite text : " + prereq_str)
    print("Forbidden overlaps : " + str(forbidden_overlaps))
    print("Forbidden overlaps text : " + forbidden_str)

    for i, split in enumerate(remaining_splits):
        print(f"Split {str(i + 1)} : {split}")
    


    # print(br_tag_indices)
    # bs_tags = list(filter(lambda elem: elem.get_text().strip() != '', course_details))
    # bs_texts = [tag.get_text().strip() for tag in bs_tags]

    # crosslisted = []
    # distributions = []
    # cross_dist_text = ('\n').join([text.strip() for text in bs_texts[:course_offering_index]])
    # crosslisted = re.findall(COURSE_RE, cross_dist_text, re.IGNORECASE)
    # distributions = re.findall(r'\(([A-Z]+-[A-Z]+[, ]*)+\)', cross_dist_text, re.IGNORECASE)
    
    # remaining_text = (' ').join([text.strip() for text in bs_texts[course_offering_index + 1:]])
    # print(remaining_text)
    # # Obtain forbidden overlaps as text
    # forbidden_re = 
    # forbidden_str = ''
    # forbidden_overlaps = set([f'{course_subject} {str(course_number)}'])
    # try:
    #     forbidden_str = re.findall(forbidden_re, remaining_text, re.DOTALL | re.IGNORECASE)[0].strip()
    #     forbidden_overlaps.update(re.findall(COURSE_RE, forbidden_str))
    # except:
    #     pass

    # prereq_re = r'Prerequisite.*?\.\s'
    # prereq_str = ''
    # prerequisites = []
    # try:    
    #     prereq_str = re.findall(prereq_re, remaining_text, re.DOTALL | re.IGNORECASE)[0].strip()
    #     prerequisites = [x for x in re.findall(COURSE_RE, prereq_str)]
    # except:
    #     pass

    # try:
    #     forbidden_split = re.split(forbidden_re, remaining_text)
    #     remaining_text = ('\n').join([text.strip() for text in forbidden_split if text.strip() != ''])
    #     prereq_split = re.split(prereq_re, remaining_text)
    #     remaining_text = ('\n').join([text.strip() for text in prereq_split if text.strip() != ''])
    # except:
    #     pass

    return {
        'name': course_name,
        'crosslisted': crosslisted,
        'distributions' : distributions,
        'seasons_offered' : seasons,
        'credits' : credits,
        'grading' : grading,
        'forbidden_overlaps' : list(forbidden_overlaps),
        'forbidden_overlaps_str' : forbidden_str,
        'prerequisites' : prerequisites,
        'prerequisites_str' : prereq_str,
        'remaining_text' : ('\n\n').join(remaining_splits),
        'raw' : raw
    }

def get_course_details(
    course : Course,
    num_retries : int = 1
):
    """Retrieves course details, as specified by Cornell's [Courses of Study 2023-2024](https://courses.cornell.edu/content.php?catoid=55&navoid=22437) page. 

    Args:
        course (Course): the course data should be queried for.
        num_retries (int, optional): the maximum number of retries that should be made for HTTP Requests to the Courses of Study page. Defaults to 1.

    Returns:
        course_data (Dict[str, Any]): data extracted from Course descriptions, in dictionary form. 
        Valid keys are ['name', 'details', 'forbidden_overlap', 'all_prereqs', 'prereq_tree']
    """
    subject = course.subject
    number = course.number

    # If Course information already exists, simply return loaded json
    course_folder = COURSE_FOLDER.format(subject = subject)
    course_file_path = COURSE_FILE_PATH.format(subject = subject, number = str(number))

    if os.path.exists(course_file_path):
        with open(course_file_path, 'r', encoding = 'utf-8') as json_file:
            json_data = json.load(json_file)
            json_file.close()
            return json_data

    # Else begin data processing
    print(f"==== RETRIEVING COURSE DETAILS FOR [{subject} {str(number)}] =====")

    # First filter Cornell University Course Descriptions (Course List 2024 - 2025) for specified course
    session = requests.Session()
    course_link = COURSE_SEARCH_2024_2025.format(subject_code = SUBJECTS[subject.upper()]['code'], code_or_number = str(number))

    # Define a function for fetching the HTML data from a provided url
    def attempt_fetch(url):
        print(url)
        try:
            # Go to the course navigator and find the data corresponding to the course received as input    
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except RequestException as e:
            print(f"> Error fetching url :\n>{url}\n>RequestException :\n{str(e)}")
            return None

    php_endpoint = None
    # for _ in range(5):
    for _ in range(num_retries):
        # After the above filtering there will only be a single course displayed
        # Obtain the href to the php script, which will contain the information desired
        soup = attempt_fetch(course_link)
        course_links = list(filter(lambda x: f'{subject} {str(number)}' in x.text, soup.find_all('a')))
            
        # Occasionally a request will yield different results
        # Although the cause for this is uncertain, retrying seems to work eventually
        if len(course_links) > 0:
            php_endpoint = course_links[0].get('href')
        if php_endpoint is not None:
            break
        
        sleep_time = 2 ** _
        print(f"Retrying in {str(sleep_time)} seconds...")
        # sleep(sleep_time)

    if php_endpoint is None:
        # raise TimeoutError("Failed to retrieve php endpoint, despite 5 retries")
        print(f"Failed to retrieve php endpoint, despite {str(num_retries)} retries")
        return {
            'name' : '',
            'details' : '',
            'forbidden_overlap' : [],
            'all_prereqs' : [],
            'prereq_tree' : {},
        }

    # Use the obtained url to the php script to obtain data
    course_data = attempt_fetch(COURSE_DETAILS_BASE + php_endpoint)

    extracted_data = None
    if course_data:
        extracted_data = parse_course_data(course_data, subject, number)
    if course_data is None:
        raise TimeoutError("Failed to retrieve php endpoint, despite multiple attempts")
    
    # Recursively get the prerequisites for the direct prerequisites of this course
    all_prereqs = extracted_data['prerequisites'].copy()
    prereq_tree = {
        prereq : get_course_details(base_str_to_course(prereq))
        for prereq in all_prereqs
    }

    # Join all recursively obtained prerequisites for this course
    for key, value in prereq_tree.items():
        all_prereqs.extend(value['all_prereqs'])
    all_prereqs = list(sorted(set(all_prereqs)))

    extracted_data['all_prereqs'] = all_prereqs
    extracted_data['prereq_tree'] = prereq_tree

    if not os.path.exists(course_folder):
        os.makedirs(course_folder)
    with open(course_file_path, 'w', encoding = 'utf-8') as json_file:
        json.dump(extracted_data, json_file, indent = 4, ensure_ascii = False)
        json_file.close()

    return extracted_data

def _process_forbidden_overlaps(courses : List[str]):
    """A function to reduce the forbidden overlaps of each course in the list of courses.
    
    Args:
        courses (List[Course]): A list of Course objects
    
    Returns:
        course_list (List[str]): A str list of reduced courses.
    """

    index = 0
    while index < len(courses):
        course = courses[index]
        forbidden_overlap = get_course_details(base_str_to_course(courses[index]))['forbidden_overlaps']
        # The forbidden overlap data for a course will include the course itself. Exclude this from removal
        # print(f"> Course : {courses[index].base_str}")

        while course in forbidden_overlap:
            forbidden_overlap.remove(course)

        print(f"> Forbidden overlap : " + (', ').join(forbidden_overlap))
        for forbidden in forbidden_overlap:
            while forbidden in courses:
                courses.remove(forbidden)

        index += 1
    return sorted(courses)

def courses_as_graph(
    courses : List[Course]
):
    nodes = list(sorted(_process_forbidden_overlaps([course.base_str for course in courses]), reverse = True))
    print("> Nodes : " + (', ').join(nodes))
    edges = list()
    
    for course in nodes:
        direct_prereqs = get_course_details(base_str_to_course(course))['prereq_tree'].keys()
        direct_prereqs = [get_course_details(base_str_to_course(direct_prereq))['forbidden_overlaps'] + [direct_prereq] for direct_prereq in direct_prereqs]
        direct_prereqs = sorted(list(set(itertools.chain.from_iterable(direct_prereqs))))
        
        print(f"> Course : {course}\n> Direct prereqs :" + (', ').join(direct_prereqs))
        
        for direct_prereq in direct_prereqs:
            if direct_prereq in nodes:
                edges.append((direct_prereq, course))

    edges = sorted(list(set(edges)))
    nodes = sorted(list(set(nodes)))
    return nodes, edges

def dag_from_ne(nodes, edges):
    G = nx.DiGraph()
    for node in nodes:
        data = get_course_details(base_str_to_course(node))
        body_text = ('\n\n').join([text for text in [data['forbidden_overlaps_str'], data['prerequisites_str'], data['remaining_text']] if text.strip() != ''])
        
        G.add_node(
            node, 
            name = data['name'],
            description = COURSE_DESCRIPTION.format(
                name = data['name'],
                crosslisted = (', ').join(data['crosslisted']) if len(data['crosslisted']) > 0 else "None",
                distributions = (', ').join(data['distributions']) if len(data['distributions']) > 0 else "None",
                seasons_offered = (', ').join(data['seasons_offered']) if len(data['seasons_offered']) > 0 else "None",
                credits = data['credits'],
                grading = data['grading'],
                body = body_text,
            ).replace('\n', '<br>') # HTML formatting for new lines
        )
    G.add_edges_from(edges)
    return G