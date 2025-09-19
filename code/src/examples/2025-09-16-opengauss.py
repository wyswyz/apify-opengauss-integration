# type: ignore

import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_openai.embeddings import OpenAIEmbeddings

from ..models import OpengaussIntegration
from .data_examples_uuid import (
    ID1, ID3, ID4A, ID4B, ID4C, ID5A, ID5B, ID5C, ID6,
    crawl_1, crawl_2, expected_results,
)
from ..vcs import compare_crawled_data_with_db
from ..vector_stores.opengauss import OpenGaussDatabase

load_dotenv()
OPENGAUSS_TABLE_NAME = os.getenv("OPENGAUSS_TABLE_NAME", "apify")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

DROP_AND_INSERT = True

db = OpenGaussDatabase(
    actor_input=OpengaussIntegration(
        opengaussHost=os.getenv("OPENGAUSS_HOST"),
        opengaussPort=os.getenv("OPENGAUSS_PORT"),
        opengaussUser=os.getenv("OPENGAUSS_USER"),
        opengaussPassword=os.getenv("OPENGAUSS_PASSWORD"),
        opengaussDBname=os.getenv("OPENGAUSS_DBNAME"),
        opengaussTableName=OPENGAUSS_TABLE_NAME,
        embeddingsProvider="OpenAI",
        embeddingsApiKey=os.getenv("OPENAI_API_KEY"),
        datasetFields=["text"],
    ),
    embeddings=embeddings,
)


def wait_for_index(sec: float = 1.0):
    time.sleep(sec)


if DROP_AND_INSERT:
    db.delete_all()
    r = db.similarity_search("text", k=100)
    print("Initial results count:", len(r))

    inserted = db.add_documents(documents=crawl_1, ids=[d.metadata["chunk_id"] for d in crawl_1])
    print("Inserted ids:", inserted)
    wait_for_index()

r = db.similarity_search("text", k=100)
print("Search results:", r)
print("Search results count:", len(r))

res = db.search_by_vector(db.dummy_vector, k=10)
print("Objects in the database:", len(res), res)
assert len(res) == 6, "Expected 6 objects in the database"

data_add, ids_update_last_seen, ids_del = compare_crawled_data_with_db(db, crawl_2)

print("Data to add", data_add)
print("Ids to update", ids_update_last_seen)
print("Ids to delete", ids_del)

assert len(data_add) == 4, "Expected 4 objects to add"
assert data_add[0].metadata["chunk_id"] == ID4C
assert data_add[1].metadata["chunk_id"] == ID5B
assert data_add[2].metadata["chunk_id"] == ID5C
assert data_add[3].metadata["chunk_id"] == ID6

assert len(ids_update_last_seen) == 1, "Expected 1 object to update"
assert ID3 in ids_update_last_seen, f"Expected {ID3} to be updated"

assert len(ids_del) == 3, "Expected 3 objects to delete"
assert ID4A in ids_del, f"Expected {ID4A} to be deleted"
assert ID4B in ids_del, f"Expected {ID4B} to be deleted"
assert ID5A in ids_del, f"Expected {ID5A} to be deleted"

# Delete data that were removed
db.delete(ids_del)
wait_for_index()
res = db.search_by_vector(db.dummy_vector, k=10)
print("Database objects after delete: ", len(res), res)
assert len(res) == 3, "Expected 3 objects in the database after deletion"

# Add new data
r = db.add_documents(data_add, ids=[d.metadata["chunk_id"] for d in data_add])
wait_for_index()
res = db.search_by_vector(db.dummy_vector, k=10)
print("Database objects after adding new", len(res), res)
ids = [r.metadata["chunk_id"] for r in res]
assert len(res) == 7, "Expected 7 objects in the database after addition"
assert ID4C in ids and ID5B in ids and ID5C in ids, "Expected new chunk_ids to be present"

# Update metadata (last_seen_at)
ts = int(datetime.now(timezone.utc).timestamp())
res = db.search_by_vector(db.dummy_vector, k=10)
# precondition in examples: ID3 initially has last_seen_at == 1
assert next(r for r in res if r.metadata["chunk_id"] == ID3).metadata["last_seen_at"] == 1

db.update_last_seen_at(ids_update_last_seen)
wait_for_index()

res = db.search_by_vector(db.dummy_vector, k=10)
assert len(res) == 7, "Expected 7 objects after metadata update"
assert next(r for r in res if r.metadata["chunk_id"] == ID3).metadata["last_seen_at"] >= ts, f"Expected {ID3} to be updated"

# delete expired objects
db.delete_expired(expired_ts=1)
wait_for_index()

res = db.search_by_vector(db.dummy_vector, k=10)
res = [r for r in res]
print("Database objects after all updates", len(res), res)
assert len(res) == 6, "Expected 6 objects after all updates"
assert next((r for r in res if r.metadata["chunk_id"] == ID1), None) is None, f"Expected {ID1} to be deleted"

# compare results with expected results
for r in expected_results:
    d = db.get_by_id(r.metadata["chunk_id"])
    assert d is not None, f"Expected document {r.metadata['chunk_id']} to exist"
    metadata = d.metadata
    assert metadata["item_id"] == r.metadata["item_id"], f"Expected item_id {r.metadata['item_id']}"
    assert metadata["checksum"] == r.metadata["checksum"], f"Expected checksum {r.metadata['checksum']}"

print("DONE")