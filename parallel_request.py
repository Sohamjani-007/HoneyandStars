import threading
from blog.models import Post
from django.db import transaction

LOCK = threading.Lock()

def create_model_entry(data):
    with transaction.atomic():
        # Use a database transaction to ensure that only one request at a time
        # can create the new entry.
        with LOCK:
            # Use a lock to ensure that only one thread at a time can execute
            # this block of code.
            existing_entries = Post.objects.filter(author=data["author_id"], title=data["title"])
            if existing_entries.exists():
                # An entry with the same field value already exists.
                return "Found Existing Entries"
            else:
                new_entry = Post.objects.create(**data)
                new_entry.save()


def my_view(request):
    data_list = [
        { "author_id": 1, "title": "Oppenheimer"},
        {"author_id": 1, "title": "US VS Russia"},
        {"author_id": 1, "title": "TOP G'S"},
    ]
    for data in data_list:
        create_model_entry(data)
    return {"success": True}
