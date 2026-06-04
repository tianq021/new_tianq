# -*- coding: utf-8 -*-
from backend.services.tool_store_db import load_tools_by_source


def load_tools_data():
    """Load enabled local tools from MySQL only."""
    return load_tools_by_source("local")
