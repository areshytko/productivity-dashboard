
from typing import Any

import jsonschema


class JsonData:
    """
    @TODO: add allOf validation semantics for inheritance
    """

    schema = {
        "$schema": "http://json-schema.org/schema#"
    }

    def __init__(self, data: Any):
        jsonschema.validate(instance=data, schema=self.schema)
        self.data = data
