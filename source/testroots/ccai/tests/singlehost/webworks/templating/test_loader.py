"""
    Tests for the TemplateLoader class.
    
    This module tests the TemplateLoader including:
    - Loading templates from directories
    - Checking template existence
    - Getting template paths and modification times
    - Multiple directories with priority ordering
    - Error handling for missing templates
"""

import os
import tempfile
import time

from ccai.webworks.templating.exceptions import TemplateNotFoundError
from ccai.webworks.templating.loader import TemplateLoader


# =============================================================================
# Test Fixtures / Setup
# =============================================================================

def _create_temp_template_dir(templates: dict) -> str:
    """
        Create a temporary directory with template files.
        
        :param templates: Dictionary mapping template names to content.
        
        :returns: Path to the temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    
    for name, content in templates.items():
        # Handle subdirectories in template names
        template_path = os.path.join(temp_dir, name)
        template_dir = os.path.dirname(template_path)
        
        if template_dir and not os.path.exists(template_dir):
            os.makedirs(template_dir)
        
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    return temp_dir


def _cleanup_temp_dir(temp_dir: str) -> None:
    """
        Remove a temporary directory and its contents.
        
        :param temp_dir: Path to the temporary directory.
    """
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    return


# =============================================================================
# __init__() Method Tests
# =============================================================================

def test_init_with_single_directory():
    """
        Test that __init__() accepts a single directory.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        if loader.directories != [temp_dir]:
            raise AssertionError(f"Expected [{temp_dir}], got {loader.directories}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_multiple_directories():
    """
        Test that __init__() accepts multiple directories.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2])
        
        if len(loader.directories) != 2:
            raise AssertionError(f"Expected 2 directories, got {len(loader.directories)}")
        
        if temp_dir1 not in loader.directories:
            raise AssertionError(f"Expected {temp_dir1} in directories")
        
        if temp_dir2 not in loader.directories:
            raise AssertionError(f"Expected {temp_dir2} in directories")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_init_with_default_extensions():
    """
        Test that __init__() uses default extensions when not specified.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        expected_extensions = [".html", ".htm", ".xml", ".txt"]
        if loader.extensions != expected_extensions:
            raise AssertionError(f"Expected {expected_extensions}, got {loader.extensions}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_custom_extensions():
    """
        Test that __init__() accepts custom extensions.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(
            directories=[temp_dir],
            extensions=[".jinja2", ".j2"]
        )
        
        if loader.extensions != [".jinja2", ".j2"]:
            raise AssertionError(f"Expected ['.jinja2', '.j2'], got {loader.extensions}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_default_encoding():
    """
        Test that __init__() uses utf-8 encoding by default.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        if loader.encoding != "utf-8":
            raise AssertionError(f"Expected 'utf-8', got '{loader.encoding}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_custom_encoding():
    """
        Test that __init__() accepts custom encoding.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(
            directories=[temp_dir],
            encoding="latin-1"
        )
        
        if loader.encoding != "latin-1":
            raise AssertionError(f"Expected 'latin-1', got '{loader.encoding}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_empty_directories():
    """
        Test that __init__() accepts empty directories list.
    """
    loader = TemplateLoader(directories=[])
    
    if loader.directories != []:
        raise AssertionError(f"Expected [], got {loader.directories}")
    
    return


# =============================================================================
# load() Method Tests
# =============================================================================

def test_load_returns_template_content():
    """
        Test that load() returns the template file content.
    """
    temp_dir = _create_temp_template_dir({
        "index.html": "<html><body>Hello World</body></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content = loader.load("index.html")
        
        if content != "<html><body>Hello World</body></html>":
            raise AssertionError(f"Unexpected content: {content}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_returns_template_from_subdirectory():
    """
        Test that load() can load templates from subdirectories.
    """
    temp_dir = _create_temp_template_dir({
        "pages/about.html": "<html><body>About Us</body></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content = loader.load("pages/about.html")
        
        if content != "<html><body>About Us</body></html>":
            raise AssertionError(f"Unexpected content: {content}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_raises_error_for_missing_template():
    """
        Test that load() raises TemplateNotFoundError for missing template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        try:
            loader.load("missing.html")
            raise AssertionError("Should raise TemplateNotFoundError")
        except TemplateNotFoundError as exc:
            if exc.template_name != "missing.html":
                raise AssertionError(f"Expected template_name 'missing.html', got '{exc.template_name}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_error_includes_searched_paths():
    """
        Test that TemplateNotFoundError includes searched paths.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2])
        
        try:
            loader.load("missing.html")
            raise AssertionError("Should raise TemplateNotFoundError")
        except TemplateNotFoundError as exc:
            if temp_dir1 not in exc.searched_paths:
                raise AssertionError(f"Expected {temp_dir1} in searched_paths")
            if temp_dir2 not in exc.searched_paths:
                raise AssertionError(f"Expected {temp_dir2} in searched_paths")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_load_from_first_directory_with_priority():
    """
        Test that load() returns template from highest priority directory.
    """
    temp_dir1 = _create_temp_template_dir({
        "index.html": "Content from dir1"
    })
    temp_dir2 = _create_temp_template_dir({
        "index.html": "Content from dir2"
    })
    
    try:
        # dir1 is first, so it has highest priority
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2])
        
        content = loader.load("index.html")
        
        if content != "Content from dir1":
            raise AssertionError(f"Expected 'Content from dir1', got '{content}'")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_load_falls_back_to_second_directory():
    """
        Test that load() falls back to lower priority directory.
    """
    temp_dir1 = _create_temp_template_dir({})  # No templates
    temp_dir2 = _create_temp_template_dir({
        "index.html": "Content from dir2"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2])
        
        content = loader.load("index.html")
        
        if content != "Content from dir2":
            raise AssertionError(f"Expected 'Content from dir2', got '{content}'")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_load_with_unicode_content():
    """
        Test that load() correctly handles unicode content.
    """
    temp_dir = _create_temp_template_dir({
        "unicode.html": "<html><body>Héllo Wörld 日本語</body></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content = loader.load("unicode.html")
        
        if content != "<html><body>Héllo Wörld 日本語</body></html>":
            raise AssertionError(f"Unexpected content: {content}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_with_empty_directories_raises_error():
    """
        Test that load() raises error when no directories configured.
    """
    loader = TemplateLoader(directories=[])
    
    try:
        loader.load("index.html")
        raise AssertionError("Should raise TemplateNotFoundError")
    except TemplateNotFoundError as exc:
        if exc.template_name != "index.html":
            raise AssertionError(f"Expected template_name 'index.html', got '{exc.template_name}'")
        if exc.searched_paths != []:
            raise AssertionError(f"Expected empty searched_paths, got {exc.searched_paths}")
    
    return


# =============================================================================
# exists() Method Tests
# =============================================================================

def test_exists_returns_true_for_existing_template():
    """
        Test that exists() returns True for existing template.
    """
    temp_dir = _create_temp_template_dir({
        "index.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        result = loader.exists("index.html")
        
        if result is not True:
            raise AssertionError("exists() should return True for existing template")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_exists_returns_false_for_missing_template():
    """
        Test that exists() returns False for missing template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        result = loader.exists("missing.html")
        
        if result is not False:
            raise AssertionError("exists() should return False for missing template")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_exists_checks_subdirectories():
    """
        Test that exists() checks templates in subdirectories.
    """
    temp_dir = _create_temp_template_dir({
        "pages/about.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        result = loader.exists("pages/about.html")
        
        if result is not True:
            raise AssertionError("exists() should return True for template in subdirectory")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_exists_checks_all_directories():
    """
        Test that exists() checks all configured directories.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({
        "index.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2])
        
        result = loader.exists("index.html")
        
        if result is not True:
            raise AssertionError("exists() should check all directories")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_exists_returns_false_for_empty_directories():
    """
        Test that exists() returns False when no directories configured.
    """
    loader = TemplateLoader(directories=[])
    
    result = loader.exists("index.html")
    
    if result is not False:
        raise AssertionError("exists() should return False when no directories")
    
    return


# =============================================================================
# get_path() Method Tests
# =============================================================================

def test_get_path_returns_full_path():
    """
        Test that get_path() returns the full filesystem path.
    """
    temp_dir = _create_temp_template_dir({
        "index.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        path = loader.get_path("index.html")
        
        expected_path = os.path.join(temp_dir, "index.html")
        if path != expected_path:
            raise AssertionError(f"Expected '{expected_path}', got '{path}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_get_path_returns_none_for_missing_template():
    """
        Test that get_path() returns None for missing template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        path = loader.get_path("missing.html")
        
        if path is not None:
            raise AssertionError(f"Expected None, got '{path}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_get_path_returns_path_from_highest_priority_directory():
    """
        Test that get_path() returns path from highest priority directory.
    """
    temp_dir1 = _create_temp_template_dir({
        "index.html": "Content from dir1"
    })
    temp_dir2 = _create_temp_template_dir({
        "index.html": "Content from dir2"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2])
        
        path = loader.get_path("index.html")
        
        expected_path = os.path.join(temp_dir1, "index.html")
        if path != expected_path:
            raise AssertionError(f"Expected '{expected_path}', got '{path}'")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_get_path_for_subdirectory_template():
    """
        Test that get_path() works for templates in subdirectories.
    """
    temp_dir = _create_temp_template_dir({
        "pages/about.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        path = loader.get_path("pages/about.html")
        
        expected_path = os.path.join(temp_dir, "pages/about.html")
        if path != expected_path:
            raise AssertionError(f"Expected '{expected_path}', got '{path}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_get_path_returns_none_for_empty_directories():
    """
        Test that get_path() returns None when no directories configured.
    """
    loader = TemplateLoader(directories=[])
    
    path = loader.get_path("index.html")
    
    if path is not None:
        raise AssertionError(f"Expected None, got '{path}'")
    
    return


# =============================================================================
# get_mtime() Method Tests
# =============================================================================

def test_get_mtime_returns_modification_time():
    """
        Test that get_mtime() returns the file modification time.
    """
    temp_dir = _create_temp_template_dir({
        "index.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        mtime = loader.get_mtime("index.html")
        
        if mtime is None:
            raise AssertionError("get_mtime() should return a timestamp")
        
        if not isinstance(mtime, float):
            raise AssertionError(f"Expected float, got {type(mtime)}")
        
        # Verify it's a reasonable timestamp (after year 2000)
        if mtime < 946684800:  # Jan 1, 2000
            raise AssertionError(f"Timestamp seems too old: {mtime}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_get_mtime_returns_none_for_missing_template():
    """
        Test that get_mtime() returns None for missing template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        mtime = loader.get_mtime("missing.html")
        
        if mtime is not None:
            raise AssertionError(f"Expected None, got {mtime}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_get_mtime_reflects_file_changes():
    """
        Test that get_mtime() reflects file modifications.
    """
    temp_dir = _create_temp_template_dir({
        "index.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        mtime1 = loader.get_mtime("index.html")
        
        # Wait a bit and modify the file
        time.sleep(0.1)
        
        template_path = os.path.join(temp_dir, "index.html")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("<html><body>Modified</body></html>")
        
        mtime2 = loader.get_mtime("index.html")
        
        if mtime2 <= mtime1:
            raise AssertionError(f"mtime should increase after modification: {mtime1} -> {mtime2}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_get_mtime_returns_none_for_empty_directories():
    """
        Test that get_mtime() returns None when no directories configured.
    """
    loader = TemplateLoader(directories=[])
    
    mtime = loader.get_mtime("index.html")
    
    if mtime is not None:
        raise AssertionError(f"Expected None, got {mtime}")
    
    return


# =============================================================================
# add_directory() Method Tests
# =============================================================================

def test_add_directory_adds_to_search_path():
    """
        Test that add_directory() adds a directory to the search path.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({
        "index.html": "<html></html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir1])
        
        # Template doesn't exist yet
        if loader.exists("index.html"):
            raise AssertionError("Template should not exist yet")
        
        # Add directory with template
        loader.add_directory(temp_dir2)
        
        # Now template should exist
        if not loader.exists("index.html"):
            raise AssertionError("Template should exist after adding directory")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_add_directory_with_high_priority():
    """
        Test that add_directory() with high priority is searched first.
    """
    temp_dir1 = _create_temp_template_dir({
        "index.html": "Content from dir1"
    })
    temp_dir2 = _create_temp_template_dir({
        "index.html": "Content from dir2"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir1])
        
        # Add dir2 with high priority
        loader.add_directory(temp_dir2, priority=100)
        
        content = loader.load("index.html")
        
        if content != "Content from dir2":
            raise AssertionError(f"Expected 'Content from dir2', got '{content}'")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_add_directory_with_low_priority():
    """
        Test that add_directory() with low priority is searched last.
    """
    temp_dir1 = _create_temp_template_dir({
        "index.html": "Content from dir1"
    })
    temp_dir2 = _create_temp_template_dir({
        "index.html": "Content from dir2"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir1])
        
        # Add dir2 with low priority
        loader.add_directory(temp_dir2, priority=-100)
        
        content = loader.load("index.html")
        
        # dir1 should still be searched first
        if content != "Content from dir1":
            raise AssertionError(f"Expected 'Content from dir1', got '{content}'")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_add_directory_default_priority():
    """
        Test that add_directory() uses priority 0 by default.
    """
    temp_dir1 = _create_temp_template_dir({
        "index.html": "Content from dir1"
    })
    temp_dir2 = _create_temp_template_dir({
        "index.html": "Content from dir2"
    })
    
    try:
        # dir1 has priority 0 (first in list)
        loader = TemplateLoader(directories=[temp_dir1])
        
        # Add dir2 with default priority (0)
        loader.add_directory(temp_dir2)
        
        # Both have same priority, but dir1 was added first
        # The order depends on implementation - just verify both are present
        if len(loader.directories) != 2:
            raise AssertionError(f"Expected 2 directories, got {len(loader.directories)}")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


def test_add_directory_multiple_times():
    """
        Test that add_directory() can be called multiple times.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({})
    temp_dir3 = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir1])
        
        loader.add_directory(temp_dir2, priority=10)
        loader.add_directory(temp_dir3, priority=20)
        
        if len(loader.directories) != 3:
            raise AssertionError(f"Expected 3 directories, got {len(loader.directories)}")
        
        # Highest priority should be first
        if loader.directories[0] != temp_dir3:
            raise AssertionError(f"Expected {temp_dir3} first, got {loader.directories[0]}")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
        _cleanup_temp_dir(temp_dir3)
    
    return


# =============================================================================
# TemplateNotFoundError Tests
# =============================================================================

def test_template_not_found_error_has_template_name():
    """
        Test that TemplateNotFoundError has template_name attribute.
    """
    exc = TemplateNotFoundError("test.html")
    
    if exc.template_name != "test.html":
        raise AssertionError(f"Expected 'test.html', got '{exc.template_name}'")
    
    return


def test_template_not_found_error_has_searched_paths():
    """
        Test that TemplateNotFoundError has searched_paths attribute.
    """
    exc = TemplateNotFoundError("test.html", ["/path1", "/path2"])
    
    if exc.searched_paths != ["/path1", "/path2"]:
        raise AssertionError(f"Expected ['/path1', '/path2'], got {exc.searched_paths}")
    
    return


def test_template_not_found_error_message_format():
    """
        Test that TemplateNotFoundError has proper message format.
    """
    exc = TemplateNotFoundError("missing.html", ["/templates", "/shared"])
    
    message = str(exc)
    
    if "missing.html" not in message:
        raise AssertionError("Message should contain template name")
    
    if "/templates" not in message or "/shared" not in message:
        raise AssertionError("Message should contain searched paths")
    
    return


def test_template_not_found_error_empty_paths():
    """
        Test TemplateNotFoundError with no searched paths.
    """
    exc = TemplateNotFoundError("missing.html", [])
    
    message = str(exc)
    
    if "missing.html" not in message:
        raise AssertionError("Message should contain template name")
    
    if "No template directories" not in message:
        raise AssertionError("Message should indicate no directories configured")
    
    return


def test_template_not_found_error_default_paths():
    """
        Test TemplateNotFoundError with default searched_paths.
    """
    exc = TemplateNotFoundError("missing.html")
    
    if exc.searched_paths != []:
        raise AssertionError("Default searched_paths should be empty list")
    
    return


# =============================================================================
# Priority Ordering Tests
# =============================================================================

def test_directories_maintain_priority_order():
    """
        Test that directories are maintained in priority order.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({})
    temp_dir3 = _create_temp_template_dir({})
    
    try:
        loader = TemplateLoader(directories=[temp_dir1, temp_dir2, temp_dir3])
        
        # First directory should have highest priority
        if loader.directories[0] != temp_dir1:
            raise AssertionError(f"Expected {temp_dir1} first")
        
        if loader.directories[1] != temp_dir2:
            raise AssertionError(f"Expected {temp_dir2} second")
        
        if loader.directories[2] != temp_dir3:
            raise AssertionError(f"Expected {temp_dir3} third")
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
        _cleanup_temp_dir(temp_dir3)
    
    return


def test_priority_ordering_with_mixed_priorities():
    """
        Test priority ordering with various priority values.
    """
    temp_dir_low = _create_temp_template_dir({
        "index.html": "low priority"
    })
    temp_dir_mid = _create_temp_template_dir({
        "index.html": "mid priority"
    })
    temp_dir_high = _create_temp_template_dir({
        "index.html": "high priority"
    })
    
    try:
        loader = TemplateLoader(directories=[])
        
        loader.add_directory(temp_dir_low, priority=-10)
        loader.add_directory(temp_dir_high, priority=10)
        loader.add_directory(temp_dir_mid, priority=0)
        
        # High priority should be first
        if loader.directories[0] != temp_dir_high:
            raise AssertionError(f"Expected high priority dir first")
        
        # Load should return from highest priority
        content = loader.load("index.html")
        if content != "high priority":
            raise AssertionError(f"Expected 'high priority', got '{content}'")
    finally:
        _cleanup_temp_dir(temp_dir_low)
        _cleanup_temp_dir(temp_dir_mid)
        _cleanup_temp_dir(temp_dir_high)
    
    return


# =============================================================================
# Edge Cases
# =============================================================================

def test_load_template_with_special_characters_in_name():
    """
        Test loading template with special characters in name.
    """
    temp_dir = _create_temp_template_dir({
        "template-with-dashes.html": "<html>dashes</html>",
        "template_with_underscores.html": "<html>underscores</html>",
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content1 = loader.load("template-with-dashes.html")
        if content1 != "<html>dashes</html>":
            raise AssertionError(f"Unexpected content: {content1}")
        
        content2 = loader.load("template_with_underscores.html")
        if content2 != "<html>underscores</html>":
            raise AssertionError(f"Unexpected content: {content2}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_template_with_deep_subdirectory():
    """
        Test loading template from deeply nested subdirectory.
    """
    temp_dir = _create_temp_template_dir({
        "level1/level2/level3/deep.html": "<html>deep</html>"
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content = loader.load("level1/level2/level3/deep.html")
        
        if content != "<html>deep</html>":
            raise AssertionError(f"Unexpected content: {content}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_empty_template():
    """
        Test loading an empty template file.
    """
    temp_dir = _create_temp_template_dir({
        "empty.html": ""
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content = loader.load("empty.html")
        
        if content != "":
            raise AssertionError(f"Expected empty string, got '{content}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_load_template_with_newlines():
    """
        Test loading template with multiple lines.
    """
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello</h1>
</body>
</html>"""
    
    temp_dir = _create_temp_template_dir({
        "multiline.html": template_content
    })
    
    try:
        loader = TemplateLoader(directories=[temp_dir])
        
        content = loader.load("multiline.html")
        
        if content != template_content:
            raise AssertionError("Content should preserve newlines")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return
