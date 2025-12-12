import threading
import random
import time
import xml.etree.ElementTree as ET
import os

# --------------------------
#   ITStudent Class
# --------------------------
class ITStudent:
    def __init__(self, name="", student_id="", programme="", courses=None):
        self.name = name
        self.student_id = student_id
        self.programme = programme
        self.courses = courses if courses else {}  # {course: mark}

    def average(self):
        return sum(self.courses.values()) / len(self.courses)

    def passed(self):
        return self.average() >= 50


# --------------------------
#   Shared Buffer (Queue)
# --------------------------
BUFFER_SIZE = 10
buffer = []

mutex = threading.Semaphore(1)
empty = threading.Semaphore(BUFFER_SIZE)
full = threading.Semaphore(0)

# Directory for storing XML files
DIRECTORY = "xml_files"
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)


# --------------------------
#   XML Wrap and Unwrap
# --------------------------
def wrap_to_xml(student: ITStudent, filename: str):
    root = ET.Element("ITStudent")

    ET.SubElement(root, "Name").text = student.name
    ET.SubElement(root, "StudentID").text = student.student_id
    ET.SubElement(root, "Programme").text = student.programme

    course_list = ET.SubElement(root, "Courses")
    for course, mark in student.courses.items():
        item = ET.SubElement(course_list, "Course")
        ET.SubElement(item, "CourseName").text = course
        ET.SubElement(item, "Mark").text = str(mark)

    tree = ET.ElementTree(root)
    tree.write(filename)


def unwrap_from_xml(filename: str):
    tree = ET.parse(filename)
    root = tree.getroot()

    name = root.find("Name").text
    student_id = root.find("StudentID").text
    programme = root.find("Programme").text

    courses = {}
    for c in root.find("Courses").findall("Course"):
        course_name = c.find("CourseName").text
        mark = int(c.find("Mark").text)
        courses[course_name] = mark

    return ITStudent(name, student_id, programme, courses)


# --------------------------
#   Producer Thread
# --------------------------
class Producer(threading.Thread):
    def run(self):
        for i in range(1, 11):  # produce 10 students
            empty.acquire()
            mutex.acquire()

            # Random student data
            name = random.choice(["Mukelwe", "Seluleko", "Neliswa", "Munashe", "Tema"])
            student_id = "".join([str(random.randint(0, 9)) for _ in range(8)])
            programme = random.choice(["BSc InformationTechnology", "BSc Computer Science", "Software Engineering"])
            courses = {
                "Programming": random.randint(0, 100),
                "Networking": random.randint(0, 100),
                "Databases": random.randint(0, 100),
                "AI": random.randint(0, 100)
            }

            student = ITStudent(name, student_id, programme, courses)
            filename = os.path.join(DIRECTORY, f"student{i}.xml")

            wrap_to_xml(student, filename)

            buffer.append(i)
            print(f"[Producer] Produced student{i}.xml")

            mutex.release()
            full.release()

            time.sleep(random.uniform(0.5, 1.5))


# --------------------------
#   Consumer Thread
# --------------------------
class Consumer(threading.Thread):
    def run(self):
        for _ in range(10):  # consume 10 students
            full.acquire()
            mutex.acquire()

            student_num = buffer.pop(0)
            filename = os.path.join(DIRECTORY, f"student{student_num}.xml")

            student = unwrap_from_xml(filename)

            # Process student
            avg = student.average()
            status = "PASS" if student.passed() else "FAIL"

            print("\n===== STUDENT REPORT =====")
            print(f"Name:       {student.name}")
            print(f"Student ID: {student.student_id}")
            print(f"Programme:  {student.programme}")
            print("Courses & Marks:")
            for c, m in student.courses.items():
                print(f"  - {c}: {m}")
            print(f"Average:    {avg:.2f}")
            print(f"Result:     {status}")
            print("===========================\n")

            # Remove XML file
            os.remove(filename)

            mutex.release()
            empty.release()

            time.sleep(random.uniform(0.5, 1.5))


# --------------------------
#   Main Program
# --------------------------
if __name__ == "__main__":
    prod = Producer()
    cons = Consumer()

    prod.start()
    cons.start()

    prod.join()
    cons.join()

    print("Producer-Consumer Simulation Completed.")
