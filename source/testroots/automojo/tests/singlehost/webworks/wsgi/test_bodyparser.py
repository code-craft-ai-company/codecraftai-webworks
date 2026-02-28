"""
    Tests for the RequestBodyParser class.
    
    This module contains unit tests and property-based tests for the WSGI
    request body parser functionality.
    
    **Feature: wsgi-layer, Property 5: Request Body Parsing Round-Trip**
    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
    
    **Feature: wsgi-layer, Property 6: Request Body Size Enforcement**
    **Validates: Requirements 7.6, 7.7**
"""

import json
import random
import string
from io import BytesIO
from typing import Any, Dict, Optional

from automojo.webworks.wsgi.bodyparser import RequestBodyParser, UploadedFile
from automojo.webworks.wsgi.exceptions import BadRequestBody, RequestEntityTooLarge


# =============================================================================
# Test Helpers and Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_form_data() -> Dict[str, str]:
    """
        Generate random form data.
    """
    num_fields = random.randint(1, 10)
    rtnval: Dict[str, str] = {}
    
    for _ in range(num_fields):
        key = generate_random_string(1, 20)
        value = generate_random_string(0, 50)
        rtnval[key] = value
    
    return rtnval


def generate_random_json_data() -> Any:
    """
        Generate random JSON-serializable data.
    """
    data_type = random.choice(["dict", "list", "string", "number", "bool", "null"])
    
    if data_type == "dict":
        num_keys = random.randint(1, 5)
        rtnval: Dict[str, Any] = {}
        for _ in range(num_keys):
            key = generate_random_string(1, 15)
            value_type = random.choice(["string", "number", "bool", "null"])
            if value_type == "string":
                rtnval[key] = generate_random_string(0, 30)
            elif value_type == "number":
                rtnval[key] = random.randint(-1000, 1000)
            elif value_type == "bool":
                rtnval[key] = random.choice([True, False])
            else:
                rtnval[key] = None
        return rtnval
    elif data_type == "list":
        num_items = random.randint(0, 5)
        return [generate_random_string(1, 20) for _ in range(num_items)]
    elif data_type == "string":
        return generate_random_string(0, 50)
    elif data_type == "number":
        return random.randint(-1000, 1000)
    elif data_type == "bool":
        return random.choice([True, False])
    else:
        return None


def generate_random_file_content() -> bytes:
    """
        Generate random file content.
    """
    length = random.randint(10, 500)
    rtnval = bytes(random.randint(0, 255) for _ in range(length))
    return rtnval


def generate_random_filename() -> str:
    """
        Generate a random filename.
    """
    extensions = [".txt", ".pdf", ".jpg", ".png", ".doc", ".csv"]
    name = generate_random_string(3, 15)
    ext = random.choice(extensions)
    rtnval = name + ext
    return rtnval


def generate_random_content_type() -> str:
    """
        Generate a random content type for files.
    """
    content_types = [
        "text/plain",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/octet-stream",
    ]
    rtnval = random.choice(content_types)
    return rtnval



# =============================================================================
# Unit Tests for RequestBodyParser
# =============================================================================

def test_parse_raw_reads_body():
    """
        Test that parse_raw reads the body from wsgi.input.
    """
    parser = RequestBodyParser()
    body_content = b"test body content"
    wsgi_input = BytesIO(body_content)
    
    result = parser.parse_raw(wsgi_input, len(body_content))
    
    if result != body_content:
        errmsg = f"Expected body '{body_content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_raw_respects_content_length():
    """
        Test that parse_raw reads only content_length bytes.
    """
    parser = RequestBodyParser()
    full_content = b"test body content with extra data"
    expected_length = 17
    wsgi_input = BytesIO(full_content)
    
    result = parser.parse_raw(wsgi_input, expected_length)
    
    if len(result) != expected_length:
        errmsg = f"Expected body length {expected_length}, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_parse_raw_reads_all_when_no_content_length():
    """
        Test that parse_raw reads all data when content_length is None.
    """
    parser = RequestBodyParser()
    body_content = b"test body content"
    wsgi_input = BytesIO(body_content)
    
    result = parser.parse_raw(wsgi_input, None)
    
    if result != body_content:
        errmsg = f"Expected body '{body_content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_raw_enforces_max_size_with_content_length():
    """
        Test that parse_raw raises RequestEntityTooLarge when content_length exceeds max_size.
    """
    max_size = 100
    parser = RequestBodyParser(max_size=max_size)
    body_content = b"x" * 200
    wsgi_input = BytesIO(body_content)
    
    exception_raised = False
    try:
        parser.parse_raw(wsgi_input, len(body_content))
    except RequestEntityTooLarge as err:
        exception_raised = True
        if err.max_size != max_size:
            errmsg = f"Expected max_size {max_size}, got {err.max_size}"
            raise AssertionError(errmsg)
        if err.actual_size != len(body_content):
            errmsg = f"Expected actual_size {len(body_content)}, got {err.actual_size}"
            raise AssertionError(errmsg)
    
    if not exception_raised:
        errmsg = "Expected RequestEntityTooLarge exception"
        raise AssertionError(errmsg)
    
    return


def test_parse_raw_enforces_max_size_without_content_length():
    """
        Test that parse_raw raises RequestEntityTooLarge when body exceeds max_size.
    """
    max_size = 100
    parser = RequestBodyParser(max_size=max_size)
    body_content = b"x" * 200
    wsgi_input = BytesIO(body_content)
    
    exception_raised = False
    try:
        parser.parse_raw(wsgi_input, None)
    except RequestEntityTooLarge:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestEntityTooLarge exception"
        raise AssertionError(errmsg)
    
    return


def test_parse_form_parses_urlencoded_data():
    """
        Test that parse_form parses application/x-www-form-urlencoded data.
    """
    parser = RequestBodyParser()
    body = b"name=John&age=30&city=NYC"
    content_type = "application/x-www-form-urlencoded"
    
    result = parser.parse_form(body, content_type)
    
    if result.get("name") != "John":
        errmsg = f"Expected name='John', got '{result.get('name')}'"
        raise AssertionError(errmsg)
    
    if result.get("age") != "30":
        errmsg = f"Expected age='30', got '{result.get('age')}'"
        raise AssertionError(errmsg)
    
    if result.get("city") != "NYC":
        errmsg = f"Expected city='NYC', got '{result.get('city')}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_form_handles_empty_values():
    """
        Test that parse_form handles empty values.
    """
    parser = RequestBodyParser()
    body = b"name=&age=30"
    content_type = "application/x-www-form-urlencoded"
    
    result = parser.parse_form(body, content_type)
    
    if result.get("name") != "":
        errmsg = f"Expected name='', got '{result.get('name')}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_form_raises_on_invalid_encoding():
    """
        Test that parse_form raises BadRequestBody on invalid UTF-8.
    """
    parser = RequestBodyParser()
    body = b"\xff\xfe"  # Invalid UTF-8
    content_type = "application/x-www-form-urlencoded"
    
    exception_raised = False
    try:
        parser.parse_form(body, content_type)
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return



def test_parse_json_parses_valid_json():
    """
        Test that parse_json parses valid JSON data.
    """
    parser = RequestBodyParser()
    data = {"name": "John", "age": 30, "active": True}
    body = json.dumps(data).encode("utf-8")
    
    result = parser.parse_json(body)
    
    if result != data:
        errmsg = f"Expected {data}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_parse_json_parses_array():
    """
        Test that parse_json parses JSON arrays.
    """
    parser = RequestBodyParser()
    data = [1, 2, 3, "four", True]
    body = json.dumps(data).encode("utf-8")
    
    result = parser.parse_json(body)
    
    if result != data:
        errmsg = f"Expected {data}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_parse_json_raises_on_invalid_json():
    """
        Test that parse_json raises BadRequestBody on invalid JSON.
    """
    parser = RequestBodyParser()
    body = b"{invalid json}"
    
    exception_raised = False
    try:
        parser.parse_json(body)
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return


def test_parse_json_raises_on_invalid_encoding():
    """
        Test that parse_json raises BadRequestBody on invalid UTF-8.
    """
    parser = RequestBodyParser()
    body = b"\xff\xfe"  # Invalid UTF-8
    
    exception_raised = False
    try:
        parser.parse_json(body)
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return


def test_parse_multipart_parses_form_fields():
    """
        Test that parse_multipart parses form fields.
    """
    parser = RequestBodyParser()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="name"\r\n'
        b"\r\n"
        b"John\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="age"\r\n'
        b"\r\n"
        b"30\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    content_type = f"multipart/form-data; boundary={boundary}"
    
    form_fields, uploaded_files = parser.parse_multipart(
        BytesIO(body),
        content_type,
        len(body)
    )
    
    if form_fields.get("name") != "John":
        errmsg = f"Expected name='John', got '{form_fields.get('name')}'"
        raise AssertionError(errmsg)
    
    if form_fields.get("age") != "30":
        errmsg = f"Expected age='30', got '{form_fields.get('age')}'"
        raise AssertionError(errmsg)
    
    if len(uploaded_files) != 0:
        errmsg = f"Expected no uploaded files, got {len(uploaded_files)}"
        raise AssertionError(errmsg)
    
    return


def test_parse_multipart_parses_file_uploads():
    """
        Test that parse_multipart parses file uploads.
    """
    parser = RequestBodyParser()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    file_content = b"Hello, World!"
    body = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        b"Content-Type: text/plain\r\n"
        b"\r\n"
        + file_content + b"\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    content_type = f"multipart/form-data; boundary={boundary}"
    
    form_fields, uploaded_files = parser.parse_multipart(
        BytesIO(body),
        content_type,
        len(body)
    )
    
    if "file" not in uploaded_files:
        errmsg = "Expected 'file' in uploaded_files"
        raise AssertionError(errmsg)
    
    uploaded_file = uploaded_files["file"]
    
    if uploaded_file.filename != "test.txt":
        errmsg = f"Expected filename='test.txt', got '{uploaded_file.filename}'"
        raise AssertionError(errmsg)
    
    if uploaded_file.content_type != "text/plain":
        errmsg = f"Expected content_type='text/plain', got '{uploaded_file.content_type}'"
        raise AssertionError(errmsg)
    
    if uploaded_file.content != file_content:
        errmsg = f"Expected content='{file_content}', got '{uploaded_file.content}'"
        raise AssertionError(errmsg)
    
    if uploaded_file.size != len(file_content):
        errmsg = f"Expected size={len(file_content)}, got {uploaded_file.size}"
        raise AssertionError(errmsg)
    
    return


def test_parse_multipart_raises_on_missing_boundary():
    """
        Test that parse_multipart raises BadRequestBody when boundary is missing.
    """
    parser = RequestBodyParser()
    body = b"some content"
    content_type = "multipart/form-data"  # No boundary
    
    exception_raised = False
    try:
        parser.parse_multipart(BytesIO(body), content_type, len(body))
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return



def test_uploaded_file_read():
    """
        Test that UploadedFile.read() returns the content.
    """
    content = b"file content"
    uploaded_file = UploadedFile(
        filename="test.txt",
        content_type="text/plain",
        content=content,
        size=len(content)
    )
    
    result = uploaded_file.read()
    
    if result != content:
        errmsg = f"Expected content '{content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_encode_form_encodes_data():
    """
        Test that encode_form encodes form data correctly.
    """
    parser = RequestBodyParser()
    data = {"name": "John", "age": "30"}
    
    result = parser.encode_form(data)
    
    # The result should be URL-encoded
    if b"name=John" not in result:
        errmsg = f"Expected 'name=John' in result, got '{result}'"
        raise AssertionError(errmsg)
    
    if b"age=30" not in result:
        errmsg = f"Expected 'age=30' in result, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_encode_json_encodes_data():
    """
        Test that encode_json encodes JSON data correctly.
    """
    parser = RequestBodyParser()
    data = {"name": "John", "age": 30}
    
    result = parser.encode_json(data)
    
    # Parse the result back to verify
    parsed = json.loads(result.decode("utf-8"))
    
    if parsed != data:
        errmsg = f"Expected {data}, got {parsed}"
        raise AssertionError(errmsg)
    
    return


def test_encode_multipart_encodes_fields():
    """
        Test that encode_multipart encodes form fields correctly.
    """
    parser = RequestBodyParser()
    fields = {"name": "John", "age": "30"}
    
    body, boundary = parser.encode_multipart(fields)
    
    # Verify the boundary is in the body
    if boundary.encode("utf-8") not in body:
        errmsg = f"Expected boundary '{boundary}' in body"
        raise AssertionError(errmsg)
    
    # Verify the fields are in the body
    if b"name" not in body:
        errmsg = "Expected 'name' field in body"
        raise AssertionError(errmsg)
    
    if b"John" not in body:
        errmsg = "Expected 'John' value in body"
        raise AssertionError(errmsg)
    
    return


def test_encode_multipart_encodes_files():
    """
        Test that encode_multipart encodes file uploads correctly.
    """
    parser = RequestBodyParser()
    fields = {"name": "John"}
    file_content = b"file content"
    files = {
        "document": UploadedFile(
            filename="test.txt",
            content_type="text/plain",
            content=file_content,
            size=len(file_content)
        )
    }
    
    body, boundary = parser.encode_multipart(fields, files)
    
    # Verify the file content is in the body
    if file_content not in body:
        errmsg = "Expected file content in body"
        raise AssertionError(errmsg)
    
    # Verify the filename is in the body
    if b"test.txt" not in body:
        errmsg = "Expected filename 'test.txt' in body"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for RequestBodyParser
# =============================================================================

def test_property_form_parsing_round_trip():
    """
        Property test: Form Parsing Round-Trip
        
        For any valid form data, encoding then parsing SHALL produce equivalent data.
        
        **Feature: wsgi-layer, Property 5: Request Body Parsing Round-Trip**
        **Validates: Requirements 7.1, 7.2, 7.3**
    """
    parser = RequestBodyParser()
    
    # Run 100 iterations with random form data
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random form data
        original_data = generate_random_form_data()
        
        # Encode the data
        encoded = parser.encode_form(original_data)
        
        # Parse the encoded data
        parsed = parser.parse_form(encoded, "application/x-www-form-urlencoded")
        
        # Verify round-trip
        for key, value in original_data.items():
            if key not in parsed:
                errmsg = f"Iteration {iteration}: Missing key '{key}' after round-trip"
                raise AssertionError(errmsg)
            
            if parsed[key] != value:
                errmsg = f"Iteration {iteration}: Value mismatch for key '{key}'. Expected '{value}', got '{parsed[key]}'"
                raise AssertionError(errmsg)
    
    return


def test_property_json_parsing_round_trip():
    """
        Property test: JSON Parsing Round-Trip
        
        For any valid JSON data, encoding then parsing SHALL produce equivalent data.
        
        **Feature: wsgi-layer, Property 5: Request Body Parsing Round-Trip**
        **Validates: Requirements 7.1, 7.2, 7.5**
    """
    parser = RequestBodyParser()
    
    # Run 100 iterations with random JSON data
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random JSON data
        original_data = generate_random_json_data()
        
        # Encode the data
        encoded = parser.encode_json(original_data)
        
        # Parse the encoded data
        parsed = parser.parse_json(encoded)
        
        # Verify round-trip
        if parsed != original_data:
            errmsg = f"Iteration {iteration}: JSON round-trip mismatch. Expected {original_data}, got {parsed}"
            raise AssertionError(errmsg)
    
    return



def test_property_multipart_parsing_round_trip():
    """
        Property test: Multipart Parsing Round-Trip
        
        For any valid multipart data with form fields and files, encoding then
        parsing SHALL produce equivalent data.
        
        **Feature: wsgi-layer, Property 5: Request Body Parsing Round-Trip**
        **Validates: Requirements 7.1, 7.2, 7.4**
    """
    parser = RequestBodyParser()
    
    # Run 100 iterations with random multipart data
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random form fields
        original_fields = generate_random_form_data()
        
        # Generate random files (0-3 files)
        num_files = random.randint(0, 3)
        original_files: Dict[str, UploadedFile] = {}
        for _ in range(num_files):
            field_name = generate_random_string(3, 15)
            filename = generate_random_filename()
            content_type = generate_random_content_type()
            content = generate_random_file_content()
            original_files[field_name] = UploadedFile(
                filename=filename,
                content_type=content_type,
                content=content,
                size=len(content)
            )
        
        # Encode the data
        encoded_body, boundary = parser.encode_multipart(original_fields, original_files)
        content_type = f"multipart/form-data; boundary={boundary}"
        
        # Parse the encoded data
        parsed_fields, parsed_files = parser.parse_multipart(
            BytesIO(encoded_body),
            content_type,
            len(encoded_body)
        )
        
        # Verify form fields round-trip
        for key, value in original_fields.items():
            if key not in parsed_fields:
                errmsg = f"Iteration {iteration}: Missing field '{key}' after round-trip"
                raise AssertionError(errmsg)
            
            if parsed_fields[key] != value:
                errmsg = f"Iteration {iteration}: Field value mismatch for '{key}'. Expected '{value}', got '{parsed_fields[key]}'"
                raise AssertionError(errmsg)
        
        # Verify files round-trip
        for field_name, original_file in original_files.items():
            if field_name not in parsed_files:
                errmsg = f"Iteration {iteration}: Missing file '{field_name}' after round-trip"
                raise AssertionError(errmsg)
            
            parsed_file = parsed_files[field_name]
            
            if parsed_file.filename != original_file.filename:
                errmsg = f"Iteration {iteration}: Filename mismatch for '{field_name}'. Expected '{original_file.filename}', got '{parsed_file.filename}'"
                raise AssertionError(errmsg)
            
            if parsed_file.content != original_file.content:
                errmsg = f"Iteration {iteration}: Content mismatch for '{field_name}'. Expected {len(original_file.content)} bytes, got {len(parsed_file.content)} bytes"
                raise AssertionError(errmsg)
    
    return


def test_property_body_size_enforcement():
    """
        Property test: Request Body Size Enforcement
        
        For any request body exceeding the configured max_request_body_size,
        the parser SHALL raise RequestEntityTooLarge without processing the full body.
        
        **Feature: wsgi-layer, Property 6: Request Body Size Enforcement**
        **Validates: Requirements 7.6, 7.7**
    """
    # Run 100 iterations with random body sizes
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random max size (10-1000 bytes)
        max_size = random.randint(10, 1000)
        
        # Generate body that exceeds max size
        excess_amount = random.randint(1, 500)
        body_size = max_size + excess_amount
        body_content = bytes(random.randint(0, 255) for _ in range(body_size))
        
        parser = RequestBodyParser(max_size=max_size)
        wsgi_input = BytesIO(body_content)
        
        # Test with content_length provided
        exception_raised = False
        try:
            parser.parse_raw(wsgi_input, body_size)
        except RequestEntityTooLarge as err:
            exception_raised = True
            
            # Verify the exception contains correct information
            if err.max_size != max_size:
                errmsg = f"Iteration {iteration}: Expected max_size {max_size}, got {err.max_size}"
                raise AssertionError(errmsg)
            
            if err.actual_size != body_size:
                errmsg = f"Iteration {iteration}: Expected actual_size {body_size}, got {err.actual_size}"
                raise AssertionError(errmsg)
            
            # Verify HTTP 413 status code
            if err.status_code != 413:
                errmsg = f"Iteration {iteration}: Expected status_code 413, got {err.status_code}"
                raise AssertionError(errmsg)
        
        if not exception_raised:
            errmsg = f"Iteration {iteration}: Expected RequestEntityTooLarge for body_size={body_size}, max_size={max_size}"
            raise AssertionError(errmsg)
    
    return


def test_property_body_within_limit_succeeds():
    """
        Property test: Bodies within limit are processed successfully
        
        For any request body within the configured max_request_body_size,
        the parser SHALL process the body successfully.
        
        **Feature: wsgi-layer, Property 6: Request Body Size Enforcement**
        **Validates: Requirements 7.6, 7.7**
    """
    # Run 100 iterations with random body sizes
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random max size (100-2000 bytes)
        max_size = random.randint(100, 2000)
        
        # Generate body that is within max size
        body_size = random.randint(0, max_size)
        body_content = bytes(random.randint(0, 255) for _ in range(body_size))
        
        parser = RequestBodyParser(max_size=max_size)
        wsgi_input = BytesIO(body_content)
        
        # Should not raise exception
        try:
            result = parser.parse_raw(wsgi_input, body_size)
            
            # Verify the body was read correctly
            if result != body_content:
                errmsg = f"Iteration {iteration}: Body content mismatch. Expected {len(body_content)} bytes, got {len(result)} bytes"
                raise AssertionError(errmsg)
                
        except RequestEntityTooLarge:
            errmsg = f"Iteration {iteration}: Unexpected RequestEntityTooLarge for body_size={body_size}, max_size={max_size}"
            raise AssertionError(errmsg)
    
    return
