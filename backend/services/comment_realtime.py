# -*- coding: utf-8 -*-
import json
import queue
import threading
from collections import defaultdict
from contextlib import contextmanager


class CommentEventBroker:
    """Small in-process pub/sub broker used by the comments SSE endpoint."""

    def __init__(self):
        self._subscribers = defaultdict(set)
        self._lock = threading.Lock()

    @contextmanager
    def subscribe(self, page_key):
        event_queue = queue.Queue(maxsize=20)
        with self._lock:
            self._subscribers[page_key].add(event_queue)

        try:
            yield event_queue
        finally:
            with self._lock:
                subscribers = self._subscribers.get(page_key)
                if subscribers is not None:
                    subscribers.discard(event_queue)
                    if not subscribers:
                        self._subscribers.pop(page_key, None)

    def publish(self, page_key, event_type, data):
        message = {
            "type": event_type,
            "page_key": page_key,
            **data
        }
        with self._lock:
            subscribers = list(self._subscribers.get(page_key, ()))

        for event_queue in subscribers:
            try:
                event_queue.put_nowait(message)
            except queue.Full:
                # A slow browser only needs the newest signal because it reloads
                # the authoritative list from the REST endpoint.
                try:
                    event_queue.get_nowait()
                    event_queue.put_nowait(message)
                except (queue.Empty, queue.Full):
                    pass


comment_event_broker = CommentEventBroker()


def encode_sse(event):
    return f"event: comment-update\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
