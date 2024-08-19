import json
import html_to_json

from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz

# Define the start and end dates for the recurring events
start_date = datetime(2024, 8, 26)  # Example start date
end_date = datetime(2024, 12, 11)  # Example end date

# Define the timezone (change this to your local timezone)
local_tz = pytz.timezone("America/New_York")


def parse_html():
    """Parses HTML file into a Dict so that data can be easily read"""
    with open("Table.html", "r", encoding="utf-8") as file:
        output_dict: dict
        output_dict = html_to_json.convert(file)
        # Setup variables to loop through courses
        root_dict = (
            output_dict.get("center")[0].get("table")[0].get("tr")[0].get("tr")[1]
        )
        current_dict = root_dict

        # This list will store all courses
        course_list = list()

        # Get all course parameters
        while (
            current_dict.get("td") is not None
            and current_dict.get("td")[len(current_dict.get("td")) - 1].get("tr")
            is not None
        ):
            course_list.append(get_course_info(current_dict))
            current_dict = current_dict.get("td")[len(current_dict.get("td")) - 1].get(
                "tr"
            )[0]

        i = 0
        for x in course_list:
            if len(x) < 12:
                course_list[i] = get_additional_time(course_list[i - 1], x)
            i += 1
        return course_list


def get_course_info(course: dict):
    """Function gets all information for a course and returns a list of attributes"""
    course_attributes = list()
    i = 0
    for x in course.get("td"):
        # get current course attribute
        attribute: str
        if x.get("_value") is not None:
            attribute = x.get("_value")
        elif x.get("font") is not None:
            attribute = x.get("font")[0].get("_value")
        elif x.get("p") is not None:
            attribute = x.get("p")[0].get("_value")
        else:
            attribute = None
        course_attributes.append(attribute)
        i += 1
    return course_attributes


def get_additional_time(course: list, additional_time: list):
    """Fix additional time to have all information required for a calendar event"""
    new_list = course.copy()
    for i in range(5):
        new_list[i + 6] = additional_time[i + 4]
    return new_list


def parse_time(time_str):
    """Convert a time string to a datetime object"""
    return datetime.strptime(time_str, "%I:%M %p").time()


def parse_days(days_str):
    """Convert days string to a list of days of the week"""
    day_map = {"M": "MO", "T": "TU", "W": "WE", "R": "TH", "F": "FR"}
    return [day_map[day] for day in days_str]


def create_icalendar(courses, start_date, end_date):
    """Create an iCalendar file"""
    calendar = Calendar()

    for course in courses:
        days = parse_days(course["Days"])
        start_time_str, end_time_str = course["Time"].split(" - ")
        start_time = parse_time(start_time_str)
        end_time = parse_time(end_time_str)
        for day in days:
            current_date = start_date
            while current_date <= end_date:
                if current_date.strftime("%a").upper()[:2] in day:
                    event = Event()
                    event.name = f"{course['Course']} - {course['Title']}"
                    event.location = course["Location"]
                    event.begin = local_tz.localize(
                        datetime.combine(current_date, start_time)
                    )
                    event.end = local_tz.localize(
                        datetime.combine(current_date, end_time)
                    )
                    event.description = f"Instructor: {course['Instructor']}"

                    # Add the event to the calendar
                    calendar.events.add(event)

                # Move to the next week
                current_date += timedelta(days=1)

    return calendar


courses = list()
for x in parse_html():
    i = 0
    course = dict()
    for j in x:
        if i == 0:
            course["CRN"] = j
        elif i == 1:
            course["Course"] = j
        elif i == 2:
            course["Modality"] = j
        elif i == 3:
            course["Title"] = j
        elif i == 4:
            course["Grade Opt"] = j
        elif i == 5:
            course["Credit Hrs"] = j
        elif i == 6:
            course["Time"] = j
        elif i == 7:
            course["Days"] = j
        elif i == 8:
            course["Location"] = j
        elif i == 9:
            course["Instructor"] = j
        elif i == 10:
            course["Part of Term"] = j
        elif i == 11:
            course["Exam"] = j
        i += 1
    courses.append(course)

# Generate the iCalendar file
calendar = create_icalendar(courses, start_date, end_date)
# Save the calendar to a file
with open("courses.ics", "w", encoding="utf-8") as f:
    f.write(str(calendar))
