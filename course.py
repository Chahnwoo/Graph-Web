import inspect, os, re

class Course:
    
    @property
    def subject(self) -> str:
        return self._subject
    
    @subject.setter
    def subject(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Subject must be of type string")
        self._subject = value
    
    @property
    def number(self) -> int:
        return self._number
    
    @number.setter
    def number(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Number must be of type int")
        self._number = int(value)
    
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Name must be of type string")
        self._name = value

    @property
    def base_str(self) -> str:
        return self._base_str
    
    @base_str.setter
    def base_str(self, value : tuple):
        subject, number = value
        self._base_str = f'{str(subject)} {str(number)}'

    def __init__(self, subject : str, number : int, name : str):
        # if not isinstance(subject, str) or not isinstance(number, int) or not isinstance(name, str):
            # raise ValueError("You have set an invalid value for the class instance. Ensure that the value you have provided for 'number' is an int.")
        self.subject = subject
        self.number = number
        self.name = name
        self.base_str = (subject, number)

    def __str__(self):
        return f"[{self._subject} {str(self._number)}] {self._name}"
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._subject == other._subject and self._number == other._number
        else:
            return False
        
    def __key(self):
        return (self._subject, self._number)

    def __hash__(self):
        return hash(self.__key())
    
    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if self._subject == other._subject:
                return self._number < other._number
            else:
                return self._subject < other._subject
        else:
            raise ValueError(f'Object provided for comparison is not of class {str(self.__class__)}')

    def dict_to_courses(courses_dict):
        courses = list()
        for subject, numbers in courses_dict.items():
            courses.extend([Course(subject = subject, number = number, name = "") for number in numbers])
        return courses

    def print_courses(courses):
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_locals = caller_frame.f_locals
        for name, value in caller_locals.items():
            if value is courses:
                print(f"===== {name} =====")
        print(('\n').join([str(course) for course in courses]) + '\n')
    
    def course_json_path(course):
        return os.path.join(os.getcwd(), 'course_jsons', course.subject, f'{course.subject}_{str(course.number)}.json')
