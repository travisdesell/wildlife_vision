#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <vector>

#include <boost/filesystem.hpp>
using boost::filesystem::directory_iterator;

#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/core/core.hpp"

using namespace std;
using namespace cv;

void read_images(string directory, std::vector<Mat> &images) {
    directory_iterator end_itr;
    for (directory_iterator itr(directory); itr != end_itr; itr++) {
        if (!is_directory(itr->status())) {
            if (itr->path().leaf().c_str()[0] == '.') continue;

            images.push_back(imread( itr->path().c_str(), CV_LOAD_IMAGE_COLOR ));
        }
    }
}

void write_images(ofstream &outfile, std::vector<Mat> images) {
    for (int i = 0; i < images.size(); i++) {
        Vec3b pixel;

        for (int j = 0; j < images[i].rows; j++) {
            for (int k = 0; k < images[i].cols; k++) {
                pixel = images[i].at<Vec3b>(j,k);

                outfile.write( (char*)&pixel.val, sizeof(char) * 3 );

                cout << " " << pixel.val[0] << " " << pixel.val[1] << " " << pixel.val[2];
            }
        }
        cout << endl;
    }
}


int main(int argc, char** argv) {
    if (argc != 4) {
        cerr << "error: incorrect arguments." << endl;
        cerr << "usage: " << endl;
        cerr << "    " << argv[0] << " <positive examples> <negative examples> <binary output file>" << endl;
        exit(1);
    }

    string positives_directory = argv[1];
    string negatives_directory = argv[2];
    string binary_output_file = argv[3];

    std::vector<Mat> pos_images;
    std::vector<Mat> neg_images;

    read_images(positives_directory, pos_images);
    cout << "read " << pos_images.size() << " positive images." << endl;

    read_images(negatives_directory, neg_images);
    cout << "read " << neg_images.size() << " negative images." << endl;

    ofstream outfile;
    outfile.open(binary_output_file.c_str(), ios::out | ios::binary);

    int img_size = pos_images[0].cols;
    int vals_per_pixel = 3;

    int initial_vals[4] = { img_size, vals_per_pixel, pos_images.size(), neg_images.size() };

    outfile.write( (char*)&initial_vals, sizeof(initial_vals));

    write_images(outfile, pos_images);
    write_images(outfile, neg_images);

    outfile.close();

    return 0;
}

