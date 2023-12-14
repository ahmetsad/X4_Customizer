
from Framework.Documentation import Doc_Category_Default
_doc_category = Doc_Category_Default('Utilities')

from pathlib import Path
# Note: re was looked at, but deemed overkill when just regular
# wildcard expressions are good enough for all expected uses.
#import re
from fnmatch import fnmatch

from Framework import Utility_Wrapper, File_Manager, Cat_Hash_Exception, Print


@Utility_Wrapper(uses_paths_from_settings = False)
def Cat_Unpack(
        source_cat_path,
        dest_dir_path,
        include_pattern  = None,
        exclude_pattern  = None,
        allow_md5_errors = False
    ):
    '''
    Unpack a single catalog file, or a group if a folder given.
    When a file is in multiple catalogs, the latest one in the list
    will be used. If a file is already present at the destination,
    it is compared to the catalog version and skipped if the same.

    * source_cat_path
      - Path to the catalog file, or to a folder.
      - When a folder given, catalogs are read in X4 priority order
        according to its expected names.
    * dest_dir_path
      - Path to the folder where unpacked files are written.
    * include_pattern
      - String or list of strings, optional, wildcard patterns for file
        names to include in the unpacked output.
      - Eg. "*.xml" to unpack only xml files
      - Case is ignored.
    * exclude_pattern
      - String or list of strings, optional, wildcard patterns for file
        names to include in the unpacked output.
      - Eg. "['*.lua']" to skip lua files.
    * allow_md5_errors
      - Bool, if True then files with md5 errors will be unpacked, otherwise
        they are skipped.
      - Such errors may arise from poorly constructed catalog files.
    '''
    # Do some error checking on the paths.
    try:
        source_cat_path = Path(source_cat_path).resolve()
        assert source_cat_path.exists()
    except Exception:
        raise AssertionError('Error in the source path ({})'.format(source_cat_path))

    try:
        dest_dir_path = Path(dest_dir_path).resolve()
        # Make the dest dir if needed.
        # -Removed; create it only when a file gets unpacked, so that it
        # doesn't make a spurious folder if the bat file is launched
        # directly from the customizer folder.
        #dest_dir_path.mkdir(parents = True, exist_ok = True)
    except Exception:
        raise AssertionError('Error in the dest path ({})'.format(dest_dir_path))


    # Pack up the patterns given to always be lists or None.
    if isinstance(include_pattern, str):
        include_pattern = [include_pattern]
    if isinstance(exclude_pattern, str):
        exclude_pattern = [exclude_pattern]

        
    # Sourcing behavior depends on if a folder or file given.
    if source_cat_path.is_dir():

        # Set up a reader for the source location.
        # If this is an extension, it needs some more annotation; can
        # test for the content.xml at the path.
        extension_summary = None
        content_xml_path = source_cat_path / 'content.xml'
        if content_xml_path.exists():
            extension_summary = File_Manager.Extension_Finder.Extension_Summary(content_xml_path)

        source_reader = File_Manager.Source_Reader.Location_Source_Reader(
            location = source_cat_path,
            extension_summary = extension_summary)

        # Print how many catalogs were found.
        Print(('{} catalog files found using standard naming convention.'
               ).format(len(source_reader.catalog_file_dict)))
    else:
        # Set up an empty reader.
        source_reader = File_Manager.Source_Reader.Location_Source_Reader(
            location = None)
        # Manually add the cat path to it.
        source_reader.Add_Catalog(source_cat_path)


    # Some counts for printout at the end.
    num_writes        = 0
    num_pattern_skips = 0
    num_hash_skips    = 0
    num_md5_skips     = 0
    

    # TODO:
    # Record a json record of already extracted file hashes, for fast
    # checking them instead of re-hashing every time.

    # TODO:
    # Switch to pulling out all virtual_paths first, then use fnmatch.filter
    # on them for each pattern, then use some set operations to merge the
    # results down to the desired set of paths.
    # This would mostly be useful if switching to storing hashes from
    # prior extractions for fast comparison, as currently the hashing
    # takes far more time than the fnmatching.

    # Loop over the Cat_Entry objects; the reader takes care of
    #  cat priorities.
    # Note: virtual_path is lowercase, but cat_entry.cat_path has
    #  original case.
    for virtual_path, cat_entry in source_reader.Get_Cat_Entries().items():

        # Skip if a pattern given and this doesn't match.
        if not _Pattern_Match(virtual_path, include_pattern, exclude_pattern):
            num_pattern_skips += 1
            continue

        dest_path = dest_dir_path / cat_entry.cat_path

        # To save some effort, check if the file already exists at
        #  the dest, and if so, get its md5 hash.
        if dest_path.exists():
            existing_binary = dest_path.read_bytes()
            dest_hash = File_Manager.Cat_Reader.Get_Hash_String(existing_binary)
            # If hashes match, skip.
            # Ego uses 0's instead of a proper hash for empty files, so also
            # check that case.
            if (dest_hash == cat_entry.hash_str 
            or (not existing_binary and cat_entry.hash_str == '00000000000000000000000000000000')):
                num_hash_skips += 1
                continue

        # Make a folder for the dest if needed.
        dest_path.parent.mkdir(parents = True, exist_ok = True)

        # Get the file binary, catching any md5 error.
        # This will only throw the exception if allow_md5_errors is False.
        try:
            cat_path, file_binary = source_reader.Read_Catalog_File(
                virtual_path,
                allow_md5_error = allow_md5_errors)
        except Cat_Hash_Exception:
            num_md5_skips += 1
            continue
        
        # Write it back out to the destination.
        with open(dest_path, 'wb') as file:
            file.write(file_binary)

        # Be verbose for now.
        num_writes += 1
        Print('Extracted {}'.format(virtual_path))

        
    Print('Files written                    : {}'.format(num_writes))
    Print('Files skipped (pattern mismatch) : {}'.format(num_pattern_skips))
    Print('Files skipped (hash match)       : {}'.format(num_hash_skips))
    Print('Files skipped (md5 hash failure) : {}'.format(num_md5_skips))    

    return



@Utility_Wrapper(uses_paths_from_settings = False)
def Cat_Pack(
        source_dir_path,
        dest_cat_path,
        include_pattern = None,
        exclude_pattern = None,
        generate_sigs = True,
        separate_sigs = False,
    ):
    '''
    Packs all files in subdirectories of the given directory into a
    new catalog file.  Only subdirectories matching those used
    in the X4 file system are considered.

    * source_dir_path
      - Path to the directory holding subdirectories to pack.
      - Subdirectories are expected to match typical X4 folder names,
        eg. 'aiscripts','md', etc.
    * dest_cat_path
      - Path and name for the catalog file being generated.
      - Prefix the cat file name with 'ext_' when patching game files,
        or 'subst_' when overwriting game files.
    * include_pattern
      - String or list of strings, optional, wildcard patterns for file
        names to include in the unpacked output.
      - Eg. "*.xml" to unpack only xml files, "md/*" to  unpack only
        mission director files, etc.
      - Case is ignored.
    * exclude_pattern
      - String or list of strings, optional, wildcard patterns for file
        names to include in the unpacked output.
      - Eg. "['*.lua','*.dae']" to skip lua and dae files.
    * generate_sigs
      - Bool, if True then dummy signature files will be created.
    * separate_sigs
      - Bool, if True then any signatures will be moved to a second
        cat/dat pair suffixed with .sig.
    '''
    # Do some error checking on the paths.
    try:
        source_dir_path = Path(source_dir_path)
        assert source_dir_path.exists()
    except Exception:
        raise AssertionError('Error in the source path ({})'.format(source_dir_path))

    try:
        dest_cat_path = Path(dest_cat_path)
        # Error if it an existing folder (and not a file).
        assert not dest_cat_path.is_dir()
        # Error if it doesn't end in '.cat'.
        assert dest_cat_path.suffix == '.cat'
        # Make the dest dir if needed.
        dest_cat_path.parent.mkdir(parents = True, exist_ok = True)
    except Exception:
        raise AssertionError('Error in the dest path ({})'.format(dest_cat_path))
    

    # Pack up the patterns given to always be lists or None.
    if isinstance(include_pattern, str):
        include_pattern = [include_pattern]
    if isinstance(exclude_pattern, str):
        exclude_pattern = [exclude_pattern]


    # Prepare a new catalog.
    cat_writer = File_Manager.Cat_Writer.Cat_Writer(
                cat_path = dest_cat_path)

    # Set up a reader for the source location.
    # Assume in the general case that this is an extension, and will
    # want to grab stuff from a nested "extensions" subfolder.
    source_reader = File_Manager.Source_Reader.Location_Source_Reader(
        location = source_dir_path,
        is_extension = True)

    # Pick out the subfolders to be included.
    subfolder_names = File_Manager.Source_Reader_Local.valid_virtual_path_prefixes
    
    num_writes        = 0
    num_pattern_skips = 0
    num_folder_skips  = 0

    # Pull out all of the files.
    for virtual_path, abs_path in sorted(source_reader.Get_All_Loose_Files().items()):
        
        # Skip if a pattern given and this doesn't match.
        if not _Pattern_Match(virtual_path, include_pattern, exclude_pattern):
            num_pattern_skips += 1
            continue

        # Skip all that do not match an expected X4 subfolder.
        if not any(virtual_path.startswith(x) for x in subfolder_names):
            num_folder_skips += 1
            continue

        # Get the file binary; skip the Read_File function since that
        #  returns a semi-processed game file (eg. stripping off xml
        #  headers and such), and just want pure binary here.
        (file_path, file_binary) = source_reader.Read_Loose_File(virtual_path)
        # Pack into a game_file, expected by the cat_writer.
        game_file = File_Manager.File_Types.Misc_File(
            virtual_path = virtual_path,
            binary = file_binary )
        cat_writer.Add_File(game_file)
        
        # Be verbose for now.
        num_writes += 1
        Print('Packed {}'.format(virtual_path))


    # If no files found, skip cat creation.
    if num_writes != 0:
        # Generate the actual cat file.
        cat_writer.Write(
            generate_sigs = generate_sigs,
            separate_sigs = separate_sigs,
            )
    
    Print('Files written                    : {}'.format(num_writes))
    Print('Files skipped (pattern mismatch) : {}'.format(num_pattern_skips))
    Print('Files skipped (not x4 subdir)    : {}'.format(num_folder_skips))
    return


def _Pattern_Match(
        name, 
        include_patterns = None, 
        exclude_patterns = None
    ):
    '''
    Checks a name against the given patterns.
    Returns True on match, False on mismatch.

    * include_patterns
      - List of wildcard patterns for names to include.
      - If none given, file treated as matching, else it only needs to
        match one of these.
    * exclude_patterns
      - List of wildcard patterns for names to exclude.
    '''
    # Start with the inclusion patterns.
    match = False
    if not include_patterns:
        match = True
    else:
        for pattern in include_patterns:
            if fnmatch(name, pattern):
                match = True
                break

    # Now check exclusions.
    if exclude_patterns:
        for pattern in exclude_patterns:
            if fnmatch(name, pattern):
                match = False
                break
    return match

