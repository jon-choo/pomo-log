import os
import tempfile

# Use a throwaway database
os.environ["POMOLOG_DB"] = os.path.join(tempfile.mkdtemp(prefix="pomolog-tests-"), "test.db")
