import json
import os
import shutil
from argparse import ArgumentParser
from xfbin.structure.xfbin import ChunkReference

from xfbin import *
from xfbin.structure.nucc import NuccChunk

VERSION = 'v1.2.2'
AUTHOR = 'SutandoTsukai181'


def unpack(args):
    if not args.output:
        args.output = os.path.basename(args.input).split('.')[0]

    args.output = os.path.abspath(args.output)
    if os.path.exists(args.output):
        if (not args.force_overwrite) and input('Overwrite existing files? (Y/N) ').lower() != 'y':
            print('Aborting.')
            os.system('pause')
            return
        print(f'Removing old directory: {args.output}\n')
        shutil.rmtree(args.output)

    os.mkdir(args.output)

    if args.file_data_only:
        args.no_json = True

    # Read the file
    xfbin = read_xfbin(args.input)

    if args.sort_types:
        # Get a dictionary of chunks based on chunk type
        for k, v in xfbin.get_type_chunk_dict().items():
            # Create a folder with the chunk's type as its name
            page_path = os.path.join(args.output, k.__qualname__[len(NuccChunk.__qualname__):])
            os.mkdir(page_path)

            for c in v:
                chunk_path = os.path.join(page_path, c.name + '.' + (c.extension
                                                                     if (args.file_data_only and c.extension != '')
                                                                     else NuccChunk.get_nucc_str_short_from_type(type(c)).lower()))

                if args.verbose:
                    print(f'Writing {chunk_path} ...')

                with open(chunk_path, 'wb') as f:
                    f.write(c.get_data(args.file_data_only))
    else:
        for i, page in enumerate(xfbin.pages):
            page.cleanup()

            if not page.chunks:
                print(f'Page {i} does not contain chunks and will be skipped.')
                continue

            # Create the page's folder with the main chunk's name
            clump_chunk = page.get_chunks_by_type(NuccChunkClump)
            main_chunk = clump_chunk[0] if len(clump_chunk) else page.chunks[-1]

            page_path = os.path.join(
                args.output, f'[{i:03}] {main_chunk.name} ({NuccChunk.get_nucc_str_from_type(type(main_chunk))})')
            os.mkdir(page_path)

            # Create the page json dict
            page_json = dict()

            # Add chunks maps
            page_json['Chunk Maps'] = list(map(lambda x: x.to_dict(), page.initial_page_chunks))

            # Add chunk references
            chunk_refs = page_json['Chunk References'] = [None] * len(page.chunk_references)
            for j, cr in enumerate(page.chunk_references):
                d = chunk_refs[j] = dict()
                d['Name'] = cr.name
                d['Chunk'] = cr.chunk.to_dict()

            # Add chunks
            chunks = page_json['Chunks'] = [None] * len(page.chunks)
            for j, c in enumerate(page.chunks):
                c:NuccChunkTexture
                d = chunks[j] = dict()
                d['File Name'] = c.name + '.' + (c.extension
                                                 if (args.file_data_only and c.extension != '')
                                                 else NuccChunk.get_nucc_str_short_from_type(type(c)).lower())
                d['Version'] = c.version
                d['Chunk'] = c.to_dict()

                chunk_path = os.path.join(page_path, d['File Name'])

                if args.verbose:
                    print(f'Writing {chunk_path} ...')

                with open(chunk_path, 'wb') as f:
                    f.write(c.get_data(args.file_data_only))

            if not args.no_json:
                with open(os.path.join(page_path, '_page.json'), 'w', encoding='cp932') as f:
                    json.dump(page_json, f, ensure_ascii=False, indent=4)

    print(f'\nSuccessfully unpacked to "{args.output}"')


def repack(args):
    if not args.output:
        args.output = os.path.basename(args.input) + '.xfbin'

    args.output = os.path.abspath(args.output)
    if os.path.exists(args.output):
        if (not args.force_overwrite) and input('Overwrite existing XFBIN? (Y/N) ').lower() != 'y':
            print('Aborting.')
            os.system('pause')
            return
        print(f'Removing old XFBIN: {args.output}\n')
        os.remove(args.output)

    # Create the directory in case some path components do not exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    xfbin = Xfbin()

    for root, directories, files in os.walk(args.input):
        for d in directories:
            page_json_path = os.path.join(root, d, '_page.json')
            if not os.path.isfile(page_json_path):
                print(f'Directory "{d}"" does not have a "_page.json" and will be skipped.')
                continue

            with open(page_json_path, 'r', encoding='cp932') as f:
                page_json = json.load(f)

            # Enclose everything in a try block to avoid having to check if each json element exists or not
            try:
                page = Page()
                xfbin.pages.append(page)

                # Read chunk maps
                chunk_maps = list(map(lambda c: NuccChunk.create_from_nucc_type(
                    c['Type'], c['Path'], c['Name'], c['Version']), page_json['Chunk Maps']))

                # Read chunk references
                chunk_refs = page.chunk_references = [None] * len(page_json['Chunk References'])
                for i, ref in enumerate(page_json['Chunk References']):
                    c = ref['Chunk']
                    chunk_refs[i] = ChunkReference(
                        ref['Name'], NuccChunk.create_from_nucc_type(c['Type'], c['Path'], c['Name'], ['Version']))

                # Read chunks
                chunks = page.chunks = list()
                for ch in page_json['Chunks']:
                    c = ch['Chunk']
                    chunk = NuccChunk.create_from_nucc_type(c['Type'], c['Path'], c['Name'], c['Version'])
                    chunk_path = os.path.join(root, d, ch['File Name'])

                    if not os.path.isfile(chunk_path):
                        print(f'Chunk "{chunk_path}" does not exist and will be skipped.')
                        continue

                    chunks.append(chunk)

                    if args.verbose:
                        print(f'Reading {chunk_path} ...')

                    with open(chunk_path, 'rb') as f:
                        chunk.set_data(bytearray(f.read()), chunk_maps)
            except:
                #print(f'"_page.json" of directory "{d}" is invalid and will be skipped.')
                print

        # We only want to look in the topmost directory
        break

    write_xfbin_to_path(xfbin, args.output)
    print(f'\nSuccessfully repacked to "{args.output}"')


def main():
    print(f'xfbin_parser {VERSION}')
    print(f'By {AUTHOR}\n')

    parser = ArgumentParser(
        description="""Unpacks/Repacks nuccChunks from CyberConnect2 XFBIN container files.""")
    parser.add_argument('input', nargs='?', action='store',
                        help='path to input XFBIN file OR path to folder to repack')
    parser.add_argument('output', nargs='?', action='store',
                        help='path to output folder to extract the chunks to (defaults to a new folder with the name of the input XFBIN) '
                        'OR path to output XFBIN file when repacking (defaults to folder name + ".xfbin")')
    parser.add_argument('-f', '--force-overwrite', dest='force_overwrite', action='store_true',
                        help='overwrite old extracted files without prompting')
    parser.add_argument('-d', '--file-data-only', dest='file_data_only', action='store_true',
                        help='when possible, write each chunk\'s file data only (NTP3 for .nut, NDP3 for .nud) (will disable repacking)')
    parser.add_argument('-s', '--sort-types', dest='sort_types', action='store_true',
                        help='sort nuccChunks by type instead of page (will disable repacking)')
    parser.add_argument('-j', '--no-json', dest='no_json', action='store_true',
                        help='do not write "_page.json" for extracted pages (will disable repacking)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print info about each extracted chunk')

    args = parser.parse_args()

    if not args.input:
        print('No INPUT was given.\nAborting.')
        os.system('pause')
        return

    if os.path.isfile(args.input):
        print('INPUT is a file - Attempting to unpack...')
        unpack(args)
    elif os.path.isdir(args.input):
        print('INPUT is a folder - Attempting to repack...')
        repack(args)
    else:
        print('INPUT path does not exist.\nAborting.')
        os.system('pause')
        return

    print("Done!")


if __name__ == '__main__':
    main()
