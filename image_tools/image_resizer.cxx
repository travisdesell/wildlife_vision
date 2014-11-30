#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>

#include <boost/filesystem.hpp>
using boost::filesystem::create_directories;
using boost::filesystem::directory_iterator;
using boost::filesystem::is_directory;

#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/core/core.hpp"

using namespace std;
using namespace cv;

int main(int argc, char** argv) {
    Mat image;

    if (argc != 4) {
        cerr << "error: incorrect arguments." << endl;
        cerr << "usage: " << endl;
        cerr << "    ./" << argv[0] << " <input directory> <output directory> <img size>" << endl;
        exit(1);
    }

    string input_directory = argv[1];
    string output_directory = argv[2];
    int img_size = atoi(argv[3]);

    cout << "creating directory (if it does not exist): '" << output_directory.c_str() << "'" << endl;
    create_directories(output_directory);

    directory_iterator end_itr;
    for (directory_iterator itr(input_directory); itr != end_itr; itr++) {
        if (!is_directory(itr->status())) {
            if (itr->path().leaf().c_str()[0] == '.') continue;

            cout << "resizing file: '" << itr->path().c_str() << endl;

            ostringstream output_filename;
            output_filename << output_directory << "/" << itr->path().leaf().c_str();

            cout << "writing to:    '" << output_filename.str() << "'" << endl;

            Size size(img_size, img_size);
            Mat src = imread( itr->path().c_str() );
            Mat dst;
            resize(src, dst, size);

            imwrite(output_filename.str().c_str(), dst);
        }
    }

    return 0;
}

