#include <stdio.h>
#include <iostream>
#include <string>
#include "opencv2/core/core.hpp"
#include "opencv2/opencv.hpp"
#include "opencv2/features2d/features2d.hpp"
#include "opencv2/nonfree/features2d.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/legacy/legacy.hpp"

using namespace cv;

void readme();

void print_keypoints(std::string name, std::vector<KeyPoint> keypoints) {
    std::cout << name << " keypoints:\n";
    for (int i = 0; i < keypoints.size(); i++) {
        std::cout << keypoints[i].pt.x << ", " << keypoints[i].pt.y << ", " << keypoints[i].angle << ", " << keypoints[i].response <<  std::endl;
    }
    std::cout << "\n\n";
}


/** @function main */
int main( int argc, char** argv ) {
    if( argc != 4 )
    { readme(); return -1; }

    Mat img_1 = imread( argv[1], CV_LOAD_IMAGE_COLOR );

    if ( !img_1.data ) {
        std::cout<< " --(!) Error reading images " << std::endl;
        return -1;
    }

    //-- Step 1: Detect the keypoints using SURF Detector
    int minHessian = atoi(argv[2]);

    SurfFeatureDetector detector( minHessian );

    std::vector<KeyPoint> keypoints_1;

    detector.detect( img_1, keypoints_1 );
//    FASTX(img_1, keypoints_1, minHessian, true, FastFeatureDetector::TYPE_9_16);
    print_keypoints("img_1", keypoints_1 );


    std::cout << "keypoints_1 size: " << keypoints_1.size() << std::endl;

    //-- Step 2: Calculate descriptors (feature vectors)
    SurfDescriptorExtractor extractor;

    Mat descriptors_1;

    extractor.compute( img_1, keypoints_1, descriptors_1 );

    //-- Draw keypoints
    Mat img_keypoints_1; Mat img_keypoints_2;

    drawKeypoints( img_1, keypoints_1, img_keypoints_1, Scalar(0, 0, 255), DrawMatchesFlags::DEFAULT );



    int rows = img_1.rows, cols = img_1.cols;
    Mat testimg = Mat::zeros(rows, cols, CV_8UC3);

    int row = 150;

    for (int x = 0; x < cols; x++) {
        Vec3b pixel = img_1.at<Vec3b>(row, x);
        std::cout << "b: " << (int)pixel.val[0] << ", g: " << (int)pixel.val[1] << ", r: " << (int)pixel.val[2] << std::endl;

        img_keypoints_1.at<Vec3b>(row, x) = Vec3b(0, 0, 0);

        int b = rows * ((float)pixel.val[0] / 255.0);
        int g = rows * ((float)pixel.val[1] / 255.0);
        int r = rows * ((float)pixel.val[2] / 255.0);

        std::cout << "b_height: " << b << ", g_height: " << g << ", r_height: " << r << std::endl;

        testimg.at<Vec3b>(b, x) = Vec3b(255, 0, 0);
        testimg.at<Vec3b>(g, x) = Vec3b(0, 255, 0);
        testimg.at<Vec3b>(r, x) = Vec3b(0, 0, 255);
    }

    imshow("Test", testimg);

    //-- Show detected (drawn) keypoints
    imshow("Keypoints 1", img_keypoints_1 );
    imwrite( argv[3], img_keypoints_1 );

    waitKey(0);

    return 0;
}

/** @function readme */
void readme() {
    std::cout << " Usage: ./SURF_detector <input_image> <min_hessian> <output_image>" << std::endl;
}
