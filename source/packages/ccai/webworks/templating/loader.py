"""
    Template loader module.
    
    This module provides the TemplateLoader class for loading templates
    from configured directories. The loader supports multiple directories
    with priority ordering, allowing templates to be overridden by placing
    them in higher-priority directories.
    
    The loader provides methods for:
    - Loading template source code from files
    - Checking if templates exist
    - Resolving a template name, applying the recognized extensions
    - Getting full filesystem paths to templates
    - Getting modification times for cache invalidation
    - Adding directories with priority ordering
    
    A template name is looked up as given first. When no file has that
    exact name and the name does not already end with one of the
    recognized extensions, each recognized extension is appended in
    order, so ``"index"`` finds ``"index.html"``.
    
    Example:
        loader = TemplateLoader(
            directories=["/app/templates", "/shared/templates"],
            extensions=[".html", ".htm"],
            encoding="utf-8"
        )
        
        if loader.exists("index.html"):
            source = loader.load("index.html")
            path = loader.get_path("index.html")
            mtime = loader.get_mtime("index.html")
"""

import os
from typing import List, Optional, Tuple

from ccai.webworks.templating.exceptions import TemplateNotFoundError


class TemplateLoader:
    """
        Loads templates from configured directories.
        
        The loader searches directories in priority order (highest priority first)
        and returns the first matching template found. This allows templates to
        be overridden by placing them in higher-priority directories.
        
        Directories can be added with explicit priorities, where higher values
        indicate higher priority (searched first). Directories added without
        a priority are appended to the end of the search order.
        
        The recognized extensions let callers name a template without its
        extension: a name that matches no file exactly, and that does not
        already end with a recognized extension, is retried with each
        recognized extension appended, in the configured order. The exact
        name is always tried first, so explicit names behave as before.
        
        :ivar _directories: List of (priority, directory) tuples sorted by priority.
        :ivar _extensions: List of recognized template file extensions.
        :ivar _encoding: File encoding for reading templates.
        
        Example:
            loader = TemplateLoader(
                directories=["/app/templates", "/shared/templates"],
                extensions=[".html", ".htm"],
                encoding="utf-8"
            )
            
            # Load a template
            source = loader.load("index.html")
            
            # Check if template exists
            if loader.exists("base.html"):
                path = loader.get_path("base.html")
    """
    
    def __init__(
        self,
        directories: List[str],
        extensions: Optional[List[str]] = None,
        encoding: str = "utf-8"
    ):
        """
            Construct a template loader.
            
            :param directories: List of directories to search (in priority order).
                               The first directory has highest priority.
            :param extensions: Recognized template file extensions, tried in
                              order when a template is named without one.
                              Defaults to [".html", ".htm", ".xml", ".txt"].
            :param encoding: File encoding for reading templates. Defaults to "utf-8".
            
            Example:
                loader = TemplateLoader(
                    directories=["/app/templates", "/shared/templates"],
                    extensions=[".html", ".htm"],
                    encoding="utf-8"
                )
        """
        # Store directories with priorities (higher index = lower priority)
        # We use negative index as priority so first directory has highest priority
        self._directories: List[Tuple[int, str]] = []
        for index, directory in enumerate(directories):
            # Use negative index so first directory has highest priority
            priority = -index
            self._directories.append((priority, directory))
        
        # Sort by priority descending (highest priority first)
        self._directories.sort(key=lambda x: x[0], reverse=True)
        
        self._extensions = extensions or [".html", ".htm", ".xml", ".txt"]
        self._encoding = encoding
        return
    
    def load(self, template_name: str) -> str:
        """
            Load a template's source code.
            
            Searches configured directories in priority order and returns
            the source code of the first matching template found.
            
            :param template_name: Name/path of the template.
            
            :returns: Template source code as a string.
            
            :raises TemplateNotFoundError: If template does not exist in any
                                          configured directory.
            
            Example:
                source = loader.load("index.html")
        """
        path = self.get_path(template_name)
        
        if path is None:
            searched_paths = [directory for _, directory in self._directories]
            raise TemplateNotFoundError(
                template_name=template_name,
                searched_paths=searched_paths
            )
        
        with open(path, "r", encoding=self._encoding) as template_file:
            source = template_file.read()
        
        return source
    
    def exists(self, template_name: str) -> bool:
        """
            Check if a template exists.
            
            Searches configured directories in priority order and returns
            True if the template is found in any directory.
            
            :param template_name: Name/path of the template.
            
            :returns: True if template exists, False otherwise.
            
            Example:
                if loader.exists("base.html"):
                    source = loader.load("base.html")
        """
        return self.get_path(template_name) is not None
    
    def resolve_name(self, template_name: str) -> Optional[str]:
        """
            Resolve a template name to the name of an existing template file.
            
            The name is tried as given first. When no configured directory
            holds a file with that exact name, and the name does not already
            end with a recognized extension, each recognized extension is
            appended in order and tried. For every candidate name the
            directories are searched in priority order.
            
            :param template_name: Name/path of the template, with or without
                                  a recognized extension.
            
            :returns: The name of the matching template relative to its
                      directory (for example ``"index.html"`` for
                      ``"index"``), or None if no template matches.
            
            Example:
                resolved = loader.resolve_name("index")
                if resolved is not None:
                    source = loader.load(resolved)
        """
        resolved_name, _ = self._find_template(template_name)
        return resolved_name
    
    def get_path(self, template_name: str) -> Optional[str]:
        """
            Get the full filesystem path to a template.
            
            Searches configured directories in priority order and returns
            the full path to the first matching template found. The name is
            resolved as described in :meth:`resolve_name`, so a name given
            without a recognized extension also finds the file that has one.
            
            :param template_name: Name/path of the template.
            
            :returns: Full path if found, None otherwise.
            
            Example:
                path = loader.get_path("index.html")
                if path:
                    print(f"Template found at: {path}")
        """
        _, full_path = self._find_template(template_name)
        return full_path
            
    def _candidate_names(self, template_name: str) -> List[str]:
        """
            Build the ordered list of file names to try for a template name.
        
            The name as given always comes first. The recognized extensions
            are appended to it only when it does not already end with one of
            them, so ``"index.html"`` is never retried as ``"index.html.html"``.
            
            :param template_name: Name/path of the template.
            
            :returns: The candidate file names, in lookup order.
        """
        candidate_names = [template_name]
        
        has_recognized_extension = False
        for extension in self._extensions:
            if template_name.endswith(extension):
                has_recognized_extension = True
                break
        
        if has_recognized_extension is False:
            for extension in self._extensions:
                candidate_names.append(f"{template_name}{extension}")
        
        return candidate_names
    
    def _find_template(self, template_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
            Find the first existing template file for a template name.
            
            Candidate names are tried in the order given by
            :meth:`_candidate_names`; for each candidate the directories are
            searched in priority order.
            
            :param template_name: Name/path of the template.
            
            :returns: A ``(resolved_name, full_path)`` tuple, or
                      ``(None, None)`` when no template matches.
        """
        resolved_name: Optional[str] = None
        full_path: Optional[str] = None
        
        candidate_names = self._candidate_names(template_name)
        for candidate_name in candidate_names:
            for _, directory in self._directories:
                candidate_path = os.path.join(directory, candidate_name)
                
                if os.path.isfile(candidate_path):
                    resolved_name = candidate_name
                    full_path = candidate_path
                    break
            
            if full_path is not None:
                break
        
        return resolved_name, full_path
    
    def get_mtime(self, template_name: str) -> Optional[float]:
        """
            Get the modification time of a template file.
            
            Returns the modification timestamp of the template file,
            useful for cache invalidation.
            
            :param template_name: Name/path of the template.
            
            :returns: Modification timestamp if found, None otherwise.
            
            Example:
                mtime = loader.get_mtime("index.html")
                if mtime:
                    print(f"Last modified: {mtime}")
        """
        path = self.get_path(template_name)
        
        if path is None:
            return None
        
        return os.path.getmtime(path)
    
    def add_directory(self, directory: str, priority: int = 0) -> None:
        """
            Add a template directory.
            
            Adds a directory to the search path with the specified priority.
            Higher priority values are searched first. If no priority is
            specified, the directory is added with priority 0.
            
            :param directory: Directory path to add.
            :param priority: Priority (higher = searched first). Defaults to 0.
            
            Example:
                # Add a high-priority override directory
                loader.add_directory("/app/overrides", priority=100)
                
                # Add a low-priority fallback directory
                loader.add_directory("/shared/templates", priority=-100)
        """
        self._directories.append((priority, directory))
        
        # Re-sort by priority descending (highest priority first)
        self._directories.sort(key=lambda x: x[0], reverse=True)
        return
    
    @property
    def directories(self) -> List[str]:
        """
            Get the list of configured directories in priority order.
            
            Returns directories sorted by priority (highest priority first).
            
            :returns: List of directory paths.
            
            Example:
                for directory in loader.directories:
                    print(f"Searching: {directory}")
        """
        return [directory for _, directory in self._directories]
    
    @property
    def extensions(self) -> List[str]:
        """
            Get the list of recognized template file extensions.
            
            :returns: List of file extensions.
            
            Example:
                print(f"Recognized extensions: {loader.extensions}")
        """
        return list(self._extensions)
    
    @property
    def encoding(self) -> str:
        """
            Get the file encoding used for reading templates.
            
            :returns: File encoding string.
            
            Example:
                print(f"Encoding: {loader.encoding}")
        """
        return self._encoding
