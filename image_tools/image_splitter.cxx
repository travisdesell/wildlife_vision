#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>

#include <boost/filesystem.hpp>

#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/core/core.hpp"

using namespace std;
using namespace cv;

int main(int argc, char** argv) {
    Mat image;

    if (argc != 2) {
        cerr << "error: incorrect arguments." << endl;
        cerr << "usage: " << endl;
        cerr << "    ./" << argv[0] << " <file to split>" << endl;
        exit(1);
    }

    string filename = argv[1];
    string output_directory = filename.substr(0, filename.rfind('.'));

    cout << "creating directory: '" << output_directory.c_str() << "'" << endl;
    boost::filesystem::create_directories(output_directory);

    image = imread(argv[1],1);
    if(image.empty()) {
        cout << "Could not open or find the image" << std::endl ;
        return -1;
    }

    namedWindow("Image", CV_WINDOW_AUTOSIZE );
    imshow("Image", image);

    // get the image data
    int height = image.rows;
    int width = image.cols;

    printf("Processing a %dx%d image\n",height,width);

    cv :: Size smallSize ( 128 , 128 );

    std :: vector < Mat > smallImages ;
    namedWindow("smallImages ", CV_WINDOW_AUTOSIZE );

    for  (int y = 0 ; y < (image.rows - smallSize.height); y += smallSize.height ) {
        for  (int x =  0 ; x < (image.cols - smallSize.width); x += smallSize.width ) {
            cv::Rect rect = cv::Rect(x, y, smallSize.width, smallSize.height );

            ostringstream filename;
            filename << output_directory << "/" << x << "_" << y << ".tiff";
            
            cout << "writing to filename: '" << filename.str().c_str() << "'" << endl;

            imwrite(filename.str().c_str(), cv::Mat(image, rect));
        }
    }


    return 0;
}

