from typing import Any, Dict, List, Optional


class FormalItem:
    def __init__(self, kind: str, name: str, spec: Dict[str, Any], api_version: str = "dda.wkng.net/v1alpha1",
                 status: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.kind = kind
        self.api_version = api_version
        self.name = name
        self.spec = spec
        self.status = status if status is not None else {}
        self.metadata = metadata if metadata is not None else {}
        self.metadata['name'] = name

    def get_item(self) -> dict:
        return {
            "kind": self.kind,
            "apiVersion": self.api_version,
            "metadata": self.metadata,
            "spec": self.spec,
            "status": self.status
        }


class FormalItemsList:
    def __init__(self, items: List[Any], metadata: Optional[Dict[str, Any]] = None,
                 api_version: str = "dda.wkng.net/v1alpha1") -> None:
        self.items = items
        self.metadata = metadata if metadata is not None else {}
        self.kind = "List"
        self.api_version = api_version

    def get_item_list(self, limit: Optional[int] = None, start: Optional[int] = None) -> dict:
        start = start if start is not None else 0
        end = start + limit if limit is not None else len(self.items)
        limited_items = self.items[start:end]

        # Update metadata with pagination information
        self.metadata.update({
            "totalItems": len(self.items),
            "start": start,
            "limit": limit,
            "end": end,
        })

        return {
            "kind": self.kind,
            "apiVersion": self.api_version,
            "metadata": self.metadata,
            "items": limited_items
        }

