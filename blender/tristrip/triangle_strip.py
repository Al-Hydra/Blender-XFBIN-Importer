""" Function to generate a (not guaranteed optimal) triangle strip out
    of a set of triangles.

    Triangle strips can be required in geometry shaders or other
    applications.

    The performance and runtime of this solution is not optimal, but it is
    sufficient for small enough problems.

    Authors: Corbinian Gruber <dev.gruco0002@gmail.com>

    License: The Unlicence

        This is free and unencumbered software released into the public domain.

        Anyone is free to copy, modify, publish, use, compile, sell, or
        distribute this software, either in source code form or as a compiled
        binary, for any purpose, commercial or non-commercial, and by any
        means.

        In jurisdictions that recognize copyright laws, the author or authors
        of this software dedicate any and all copyright interest in the
        software to the public domain. We make this dedication for the benefit
        of the public at large and to the detriment of our heirs and
        successors. We intend this dedication to be an overt act of
        relinquishment in perpetuity of all present and future rights to this
        software under copyright law.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
        EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
        MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
        IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
        OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
        ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
        OTHER DEALINGS IN THE SOFTWARE.

        For more information, please refer to <https://unlicense.org>
"""


def find_strip(triangles):
    """ Finds a triangle strip representation for a given set of triangle
        faces.

    Args:
        triangles (list of triangles): A list of triangles. A triangle is
            represented by a list or tuple of 3 elements. The order of those
            elements does not matter. The elements should be comparable and
            should be able to be an element of a set.

    Returns:
        List of elements: A list consisting of the triangle elements that form
        a triangle strip covering all triangles at least once.
    """

    def find_strip_internal(current_strip, used_triangles, max_triangle_usage):

        # check if we covered all triangles by now
        unused_triangles_existing = False
        for i in range(len(triangles)):
            if used_triangles[i] == 0:
                unused_triangles_existing = True
                break

        # if we covered all triangles, we found a solution and return it
        if not unused_triangles_existing:
            return current_strip

        if len(current_strip) == 0:
            # initial state, iterate over all triangles and use each one as
            # the starting point for the recursive algorithm.
            for i, triangle in enumerate(triangles):
                # mark the triangle as used triangle (used once)
                used_triangles[i] = 1

                # Each permutation of the first triangles vertices have to
                # be tested, since their order matters.

                # add the triangles elements (vertices) to the current triangle
                # strip and recursively find adjacent triangles
                current_strip += [triangle[0], triangle[1], triangle[2]]
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)

                # if the result of that search is not none, we found a solution
                # hence return the solution
                if result is not None:
                    return result
                # otherwise undo our changes to the current triangle strip
                current_strip = current_strip[:-3]

                # and repeat the same for all other permutations
                current_strip += [triangle[0], triangle[2], triangle[1]]
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)
                if result is not None:
                    return result
                current_strip = current_strip[:-3]

                current_strip += [triangle[1], triangle[0], triangle[2]]
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)
                if result is not None:
                    return result
                current_strip = current_strip[:-3]

                current_strip += [triangle[1], triangle[2], triangle[0]]
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)
                if result is not None:
                    return result
                current_strip = current_strip[:-3]

                current_strip += [triangle[2], triangle[0], triangle[1]]
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)
                if result is not None:
                    return result
                current_strip = current_strip[:-3]

                current_strip += [triangle[2], triangle[1], triangle[0]]
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)
                if result is not None:
                    return result
                current_strip = current_strip[:-3]

                # if we checked all permutations of the current triangle and
                # none was successfull, reset the usage of the triangle and
                # try the next one
                used_triangles[i] = 0
        else:
            # non initial state
            # checking each triangle if it can be used to extend the current
            # triangle strip. Therefore the triangles strip last two vertices
            # have to be part of the triangle
            for i, triangle in enumerate(triangles):

                # check if the triangle is already covered the maximum allowed
                # amount, if this is true, we cannot use it again for the
                # solution
                if used_triangles[i] >= max_triangle_usage:
                    continue

                # check if the last two vertices of the current strip are part
                # of the current triangle
                triangle_as_set = set(triangle)
                part_of_triangle = {current_strip[-1], current_strip[-2]}
                if not triangle_as_set.issuperset(part_of_triangle):
                    # triangle does not share two of the same vertices, hence
                    # we cannot use it
                    continue

                # get the vertex that was not part of the triangle strip
                triangle_vertex = list(
                    triangle_as_set.difference(part_of_triangle))[0]

                # increase the usage of the current triangle and append its
                # vertex to the current strip
                used_triangles[i] += 1
                current_strip.append(triangle_vertex)

                # now check recursively for a solution
                result = find_strip_internal(
                    current_strip, used_triangles, max_triangle_usage)
                # if a solution was found, we return it
                if result is not None:
                    return result

                # otherwise remove the current triangle from the strip and
                # reduce its usage counter and continue with the next one.
                current_strip.pop()
                used_triangles[i] -= 1

        # if we reached here, we did not find a solution an thus return None
        return None

    # since it is possible that some triangles have to be covered twice by the
    # triangle strip in order to allow for a solution to exist, we increase the
    # allowed triangle usage / coverage until we find a solution
    usage = 1
    result = None

    # we repeat the search until we found a solution
    while result is None:
        # initialize the used / covered triangle count and set it to zero for
        # every triangle
        tmp_used_triangles = dict()
        for i in range(len(triangles)):
            tmp_used_triangles[i] = 0

        # we start out with an empty triangle strip
        tmp_triangle_strip = []
        # call our function to find a triangle strip for the given constraints
        result = find_strip_internal(
            tmp_triangle_strip, tmp_used_triangles, usage)

        # increase the allowed usage for the next check
        usage += 1

    # return the found solution
    return result


def example():
    icosahedron_triangles = [[0, 1, 2],
                             [3, 1, 0],
                             [4, 1, 3],
                             [5, 1, 4],
                             [2, 1, 5],
                             [6, 7, 8],
                             [8, 7, 9],
                             [9, 7, 10],
                             [10, 7, 11],
                             [11, 7, 6],
                             [0, 2, 6],
                             [2, 5, 11],
                             [5, 4, 10],
                             [4, 3, 9],
                             [3, 0, 8],
                             [8, 0, 6],
                             [9, 3, 8],
                             [10, 4, 9],
                             [11, 5, 10],
                             [6, 2, 11]]

    print("Trying to find a triangle strip representation of an icosahedron")
    triangle_strip = find_strip(icosahedron_triangles)
    print("Triangle strip:", triangle_strip)
    print("Length of the triangle strip:", len(triangle_strip))


if __name__ == "__main__":
    example()
