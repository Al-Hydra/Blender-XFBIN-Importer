from itertools import chain
from typing import Dict, List, Optional, Tuple, Union

from .nucc import (NuccChunk, NuccChunkClump, NuccChunkMaterial, NuccChunkModelHit, NuccChunkNull,
                   NuccChunkPage, NuccChunkTexture)


class ChunkReference:
    def __init__(self, name: str, chunk: NuccChunk):
        self.name = name
        self.chunk = chunk


class Page:
    # Only updated/used when the XFBIN is read for the first time
    # Used for writing the page's JSON to be used when repacking
    initial_page_chunks: List[NuccChunk]

    def __init__(self):
        self.chunks: List[NuccChunk] = list()
        self.chunk_references: List[ChunkReference] = list()

    def __iter__(self):
        return iter(self.chunks)

    def get_chunks_by_type(self, nucc_type: Union[str, type]) -> List[NuccChunk]:
        if type(nucc_type) is str:
            nucc_type = NuccChunk.get_nucc_type_from_str(nucc_type)

        return [c for c in self.chunks if type(c) is nucc_type]

    def clear(self):
        """Clears the Chunks list of this Page by removing every chunk."""
        self.chunks.clear()

    def cleanup(self):
        """Removes the NuccChunkNull and NuccChunkPage in this page, if they exist."""
        self.chunks = [c for c in self.chunks if not isinstance(
            c, (NuccChunkNull, NuccChunkPage))]

    def add_chunk(self, chunk: NuccChunk):
        """Adds the given NuccChunk to this Page.\n
        Chunks will be overwritten if they refer to the same chunk map (name, file path, and type match).\n
        """

        if chunk in self.chunks:
            self.chunks[self.chunks.index(chunk)] = chunk
        else:
            self.chunks.append(chunk)


class Xfbin:
    def __init__(self):
        self.pages: List[Page] = list()

    def __iter__(self):
        return iter(self.pages)

    def get_type_chunk_dict(self) -> Dict[Union[str, type], List[NuccChunk]]:
        chunks = list(chain.from_iterable(self.pages))
        result: Dict[type, List[NuccChunk]] = dict()

        for c in chunks:
            if type(c) is NuccChunkPage or type(c) is NuccChunkNull:
                continue

            if not result.get(type(c), None):
                result[type(c)] = list()

            result[type(c)].append(c)

        return result

    def get_page_chunk_dict(self) -> Dict[Union[str, type], List[NuccChunk]]:
        result = dict()

        for p in range(len(self.pages)):
            result[f'Page{p}'] = [c for c in self.pages[p].chunks if type(
                c) not in (NuccChunkPage, NuccChunkNull)]

        return result

    def get_chunks_by_type(self, nucc_type: Union[str, type]) -> List[NuccChunk]:
        result = list()

        for p in self.pages:
            result.extend(p.get_chunks_by_type(nucc_type))

        return result

    def get_pages_by_type(self, nucc_type: Union[str, type]) -> List[Page]:
        """Returns a list of pages that contain at least one chunk of the specified type."""
        return [p for p in self.pages if p.get_chunks_by_type(nucc_type)]

    def clear(self):
        """Clears the Pages list of this Xfbin by removing every Page."""
        self.pages.clear()

    def get_chunk_page(self, chunk: NuccChunk) -> Optional[Tuple[int, Page]]:
        """Returns a tuple of the index and the Page that contains a chunk map reference of the given NuccChunk, or None if it does not exist."""
        for i, page in enumerate(self.pages):
            if chunk in page.chunks:
                return (i, page)

        return None

    def update_chunk_page(self, chunk: NuccChunk):
        """Overwrites the Page that contains a chunk map reference of the given NuccChunk with the chunk.\n
        Pages will be overwritten if they have a chunk that refers to the same chunk map (name, file path, and type match).\n
        Returns a reference to the updated chunk Page, or None if no Page contained a reference to the chunk.\n
        """

        chunk_page = Page()
        chunk_page.add_chunk(chunk)

        existing_page = self.get_chunk_page(chunk)

        if existing_page:
            index, _ = existing_page
            self.pages[index] = chunk_page
            return chunk_page

        return None

    def add_chunk_page(self, chunk: NuccChunk):
        """Adds the given NuccChunk to a new Page and adds it to this Xfbin.\n
        Pages will be overwritten if they have a chunk that refers to the same chunk map (name, file path, and type match).\n
        Returns a reference to the new chunk Page.\n
        """

        result = self.update_chunk_page(chunk)

        if not result:
            self.pages.append(Page())
            self.pages[-1].add_chunk(chunk)
            return self.pages[-1]

        return result

    def remove_chunk_page(self, chunk: NuccChunk):
        """Removes the Page that contains a chunk map reference of the given NuccChunk from this Xfbin.\n
        Returns True if a Page was removed, False otherwise.\n
        """

        existing_page = self.get_chunk_page(chunk)

        if existing_page:
            index, _ = existing_page
            self.pages.pop(index)
            return True

        return False

    def add_clump_page(self, clump: NuccChunkClump) -> Page:
        """Generates and adds a clump Page to this Xfbin using the given NuccChunkClump Chunk.\n
        All of the chunk references will be addressed, and texture Pages will be created when available.\n
        Pages will be overwritten if the clump Chunks refer to the same chunk map (name, file path, and type match).\n
        Returns a reference to the new clump Page.\n
        """

        if not isinstance(clump, NuccChunkClump):
            raise Exception(
                f'Cannot add clump - {clump} is not an instance of NuccChunkClump.')

        clump_page = Page()
        materials: List[NuccChunkMaterial] = list()
        #textures: List[NuccChunkTexture] = list()
        #texture_pages: List[Page] = list()

        # Remove the old clump page if it exists
        existing_page = self.get_chunk_page(clump)
        if existing_page:
            index, _ = existing_page
            self.pages.pop(index)

        # Add the unique model chunks
        for model in list(dict.fromkeys(chain(clump.model_chunks, *clump.model_groups))):
            # Clump model groups can have None references, so skip those
            if model:
                if isinstance(model.hit_chunk, NuccChunkModelHit):
                    clump_page.add_chunk(model.hit_chunk)
                clump_page.add_chunk(model)
                materials.extend(model.material_chunks)

        # Add the coord chunks
        for coord in clump.coord_chunks:
            clump_page.add_chunk(coord)

        # Add the clump chunk
        clump_page.add_chunk(clump)

        # Add the unique material chunks
        for material in list(dict.fromkeys(materials)):
            clump_page.add_chunk(material)
            #textures.extend(list(chain(*material.texture_groups)))

        # Add the unique texture chunks
        '''for texture in list(dict.fromkeys(textures)):
            # Add each texture chunk to a new page or update its page if it exists
            # If the chunk does not have data, ignore it
            if texture.nut or texture.data:
                if not self.update_chunk_page(texture):
                    texture_pages.append(Page())
                    texture_pages[-1].add_chunk(texture)'''

        # Add the new texture pages before the clump page
        #self.pages.extend(texture_pages)
        self.pages.append(clump_page)

        return clump_page
