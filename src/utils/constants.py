"""Constants and metadata for PDFForge."""

TOOLS = [
    {
        "key": "tool_merge",
        "title": "Merge PDF",
        "description": "Combine multiple PDF documents into one.",
        "is_implemented": True,
        "quick_access": True
    },
    {
        "key": "tool_compress",
        "title": "Compress PDF",
        "description": "Reduce PDF file size where practical.",
        "is_implemented": False,
        "quick_access": True
    },
    {
        "key": "tool_convert",
        "title": "Image Conversion",
        "description": "Convert supported images and PDF pages.",
        "is_implemented": False,
        "quick_access": True
    },
    {
        "key": "tool_unlock",
        "title": "Unlock PDF",
        "description": "Open a protected PDF using an authorized password.",
        "is_implemented": False,
        "quick_access": False
    },
    {
        "key": "tool_protect",
        "title": "Protect PDF",
        "description": "Add password protection to a PDF.",
        "is_implemented": False,
        "quick_access": False
    },
    {
        "key": "tool_remove",
        "title": "Remove Pages",
        "description": "Remove selected pages from a document.",
        "is_implemented": True,
        "quick_access": True
    },
    {
        "key": "tool_reorder",
        "title": "Reorder Pages",
        "description": "Rearrange the pages in a PDF.",
        "is_implemented": True,
        "quick_access": False
    },
    {
        "key": "tool_numbers",
        "title": "Add Page Numbers",
        "description": "Number PDF pages in your preferred position.",
        "is_implemented": False,
        "quick_access": False
    }
]
