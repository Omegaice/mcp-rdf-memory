"""
Store Manager for RDF Memory Server

Handles pyoxigraph Store locking complexity through context manager pattern.
"""

import gc
from collections.abc import Generator
from contextlib import contextmanager

from pyoxigraph import Store


class StoreManager:
    """Manages pyoxigraph Store instances with proper lock handling.

    Handles the complex locking behavior where:
    - In-memory stores can be reused safely
    - Persistent stores require temporary instances to avoid process-based locks
    - Read-only stores also hold locks and need proper cleanup
    """

    def __init__(self, store_path: str | None = None) -> None:
        """Initialize store manager.

        Args:
            store_path: Path for persistent storage. If None, creates in-memory store.
        """
        self.store_path = store_path

        # For in-memory stores, create once and reuse (no locking issues)
        # For persistent stores, create NO stores at startup to avoid any locking
        if self.store_path is None:
            self.store = Store()  # In-memory store
        else:
            self.store = None  # Persistent store - will use temporary stores per operation

    @contextmanager
    def get_store(self, read_only: bool = True) -> Generator[Store, None, None]:
        """Get store instance for operations with automatic lock management.

        Args:
            read_only: If True, creates temporary read-only store for the operation.
                      If False, creates temporary write store for the operation.

        Yields:
            Store instance for the operation.
        """
        if self.store_path is None:
            # In-memory store - always use the same instance
            assert self.store is not None
            yield self.store
            return

        # Persistent store: always create temporary instances per operation
        store = None
        try:
            if read_only:
                try:
                    store = Store.read_only(self.store_path)
                except FileNotFoundError:
                    # Database doesn't exist yet - create it first with a temporary write store
                    temp_store = Store(self.store_path)
                    temp_store.flush()  # Ensure database is created
                    del temp_store  # Explicitly release
                    gc.collect()  # Force garbage collection
                    # Now open read-only
                    store = Store.read_only(self.store_path)
            else:
                # Write operations: create temporary write store for this operation only
                # This may fail if another process currently holds write lock
                # Future improvement: Add retry logic for concurrent write access
                store = Store(self.store_path)

            yield store

        finally:
            # Explicitly release store for persistent stores to release locks
            if store is not None:
                del store
                gc.collect()  # Force garbage collection to release locks
