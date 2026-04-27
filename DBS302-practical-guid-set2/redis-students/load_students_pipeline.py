import csv
import redis

# ── Step A: Establish a connection to the local Redis server ──────────────────
# By default, Redis listens on localhost at port 6379.
# decode_responses=True ensures returned values are Python strings, not bytes.
r = redis.Redis(host='localhost', port=6379, db=9, decode_responses=True)

# ── Step B: Open a pipeline with transaction disabled ─────────────────────────
# transaction=False means commands will be buffered and sent together,
# but NOT wrapped in a MULTI/EXEC block. This is ideal for non-atomic bulk inserts.
pipe = r.pipeline(transaction=False)

# ── Step C: Read the CSV file and queue HSET commands into the pipeline ───────
# No commands are sent to Redis during this loop — they are only buffered locally.
with open('students.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    count = 0
    for row in reader:
        # Construct a namespaced key: e.g., "student:STU-0001"
        key = f"student:{row['Student_No']}"

        # Queue an HSET command for each student record.
        # mapping= accepts a dictionary, storing all fields in a single call.
        pipe.hset(key, mapping={
            'Name':          row['Name'],
            'Student_No':    row['Student_No'],
            'Course':        row['Course'],
            'Admitted_year': row['Admitted_year'],
        })
        count += 1

# ── Step D: Execute all buffered commands in a single network round-trip ──────
# pipe.execute() dispatches everything at once and returns a list of results.
# Each result is 1 (if the key was newly created) or 0 (if it already existed).
results = pipe.execute()

print(f"Pipeline executed — {count} student records inserted into Redis.")
print(f"    Results summary: {results}")

# ── Step E: Verification — read back one record to confirm data integrity ─────
print("\n── Verification: reading back STU-0001 ──")
print(r.hgetall("student:STU-0001"))

# List all keys matching the student namespace
print("\n── All student keys stored in Redis ──")
for key in sorted(r.scan_iter("student:*")):
    print(f"  {key}")
