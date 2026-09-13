#include <exception>
#include <iostream>

#include "cc/load-spz.h"

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: ply_to_spz_v3 <input.ply> <output.spz>\n";
        return 1;
    }

    try {
        spz::UnpackOptions unpack_options;
        const spz::GaussianCloud splat = spz::loadSplatFromPly(argv[1], unpack_options);

        spz::PackOptions pack_options;
        pack_options.version = 3;

        if (!spz::saveSpz(splat, pack_options, argv[2])) {
            std::cerr << "Failed to save SPZ v3 file.\n";
            return 1;
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
