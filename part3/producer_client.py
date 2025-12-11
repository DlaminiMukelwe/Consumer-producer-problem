#!/usr/bin/env python3
"""
Producer (client) - generates random ITStudent XML and sends to the server.
Usage:
    python producer_client.py --host 127.0.0.1 --port 5000 --count 10
"""
import socket
import struct
import random
import time
import argparse
import xml.etree.ElementTree as ET

class ITStudent:
    def __init__(self, name="", student_id="", programme="", courses=None):
        self.name = name
        self.student_id = student_id
        self.programme = programme
        self.courses = courses if courses else {}

def wrap_to_xml_string(student: ITStudent):
    root = ET.Element("ITStudent")
    ET.SubElement(root, "Name").text = student.name
    ET.SubElement(root, "StudentID").text = student.student_id
    ET.SubElement(root, "Programme").text = student.programme
    course_list = ET.SubElement(root, "Courses")
    for course, mark in student.courses.items():
        item = ET.SubElement(course_list, "Course")
        ET.SubElement(item, "CourseName").text = course
        ET.SubElement(item, "Mark").text = str(mark)
    return ET.tostring(root, encoding="utf-8").decode("utf-8")

def send_message(sock, filename, xml_str):
    fname_bytes = filename.encode("utf-8")
    xml_bytes = xml_str.encode("utf-8")
    sock.sendall(struct.pack(">I", len(fname_bytes)))
    sock.sendall(fname_bytes)
    sock.sendall(struct.pack(">I", len(xml_bytes)))
    sock.sendall(xml_bytes)

def main(host, port, count):
    with socket.create_connection((host, port)) as sock:
        for i in range(1, count+1):
            name = random.choice(["Mukelwe", "Seluleko", "Neliswa", "Munashe", "Tema"])
            student_id = "".join([str(random.randint(0,9)) for _ in range(8)])
            programme = random.choice(["Bsc Information Technology", "BSc Computer Science", "Software Engineering"])
            courses = {
                "Programming": random.randint(0,100),
                "Networking": random.randint(0,100),
                "Databases": random.randint(0,100),
                "AI": random.randint(0,100)
            }
            student = ITStudent(name, student_id, programme, courses)
            xml_str = wrap_to_xml_string(student)
            filename = f"student{i}.xml"
            send_message(sock, filename, xml_str)
            print(f"[Producer] Sent {filename}")
            time.sleep(random.uniform(0.2, 1.0))
    print("[Producer] Done sending.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    main(args.host, args.port, args.count)
