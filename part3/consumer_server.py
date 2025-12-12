#!/usr/bin/env python3
"""
Consumer (server) - receives XML student records over TCP, processes them.
Usage:
    python consumer_server.py --host 0.0.0.0 --port 5000 --output-dir xml_files --count 10
"""
import socket
import struct
import threading
import argparse
import os
import xml.etree.ElementTree as ET

# ITStudent class (same as your original)
class ITStudent:
    def __init__(self, name="", student_id="", programme="", courses=None):
        self.name = name
        self.student_id = student_id
        self.programme = programme
        self.courses = courses if courses else {}

    def average(self):
        return sum(self.courses.values()) / len(self.courses) if self.courses else 0.0

    def passed(self):
        return self.average() >= 50

# Helpers for protocol
def recvall(conn, n):
    data = b""
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def recv_message(conn):
    # Read filename length
    raw = recvall(conn, 4)
    if not raw:
        return None, None
    (fname_len,) = struct.unpack(">I", raw)
    fname_bytes = recvall(conn, fname_len)
    if fname_bytes is None:
        return None, None
    filename = fname_bytes.decode("utf-8")

    # Read xml length
    raw = recvall(conn, 4)
    if not raw:
        return None, None
    (xml_len,) = struct.unpack(">I", raw)
    xml_bytes = recvall(conn, xml_len)
    if xml_bytes is None:
        return None, None
    xml_str = xml_bytes.decode("utf-8")
    return filename, xml_str

def unwrap_from_xml_string(xml_str):
    root = ET.fromstring(xml_str)
    name = root.find("Name").text
    student_id = root.find("StudentID").text
    programme = root.find("Programme").text
    courses = {}
    for c in root.find("Courses").findall("Course"):
        course_name = c.find("CourseName").text
        mark = int(c.find("Mark").text)
        courses[course_name] = mark
    return ITStudent(name, student_id, programme, courses)

def handle_client(conn, addr, output_dir, expected_count):
    print(f"[Server] Connection from {addr}")
    received = 0
    try:
        while expected_count is None or received < expected_count:
            result = recv_message(conn)
            if result is None:
                break
            filename, xml_str = result
            # write xml to disk (optional)
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml_str)

            student = unwrap_from_xml_string(xml_str)
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

            # remove file after processing
            try:
                os.remove(filepath)
            except OSError:
                pass

            received += 1
    finally:
        conn.close()
        print(f"[Server] Connection {addr} closed. Processed {received} student(s).")

def start_server(host, port, output_dir, expected_count=None):
    os.makedirs(output_dir, exist_ok=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[Server] Listening on {host}:{port} ...")
        while True:
            conn, addr = s.accept()
            # handle each client in a thread
            t = threading.Thread(target=handle_client, args=(conn, addr, output_dir, expected_count), daemon=True)
            t.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--output-dir", default="xml_files")
    parser.add_argument("--count", type=int, default=10,
                        help="expected number of student records per connection (optional). Set to 0 or negative for unlimited.")
    args = parser.parse_args()

    expected = args.count if args.count and args.count > 0 else None
    start_server(args.host, args.port, args.output_dir, expected)
