#include <stdio.h>
#include <iostream>
#include "opencv/highgui.h"
#include "opencv2/core/core.hpp"
#include "opencv2/features2d/features2d.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/nonfree/features2d.hpp"
#include "opencv2/legacy/legacy.hpp"

using namespace cv;


/** @function readme */
void readme(char* binary_name) { 
    std::cout << " Usage: ./" << binary_name << " <img1> <img2>" << std::endl;
}

/** @function main */
int main( int argc, char** argv )
{
    if( argc != 3 ) { 
        readme(argv[0]); return -1;
    }

    Mat img_1 = imread( argv[1], CV_LOAD_IMAGE_COLOR );
    Mat img_2 = imread( argv[2], CV_LOAD_IMAGE_COLOR );

    if ( !img_1.data || !img_2.data ) {
        std::cout<< " --(!) Error reading images " << std::endl; return -1;
    }

    //-- Step 1: Detect the keypoints using SURF Detector
    int minHessian = 500;

    SurfFeatureDetector surf_detector( minHessian );
    SiftFeatureDetector sift_detector;

    std::vector<KeyPoint> surf_keypoints_1, surf_keypoints_2, sift_keypoints_1, sift_keypoints_2;

    surf_detector.detect( img_1, surf_keypoints_1 );
    surf_detector.detect( img_2, surf_keypoints_2 );

    sift_detector.detect( img_1, sift_keypoints_1 );
    sift_detector.detect( img_2, sift_keypoints_2 );

    //-- Step 2: Calculate descriptors (feature vectors)
    SurfDescriptorExtractor surf_extractor;
    SiftDescriptorExtractor sift_extractor;

    Mat surf_descriptors_1, surf_descriptors_2;
    Mat sift_descriptors_1, sift_descriptors_2;

    surf_extractor.compute( img_1, surf_keypoints_1, surf_descriptors_1 );
    surf_extractor.compute( img_2, surf_keypoints_2, surf_descriptors_2 );

    sift_extractor.compute( img_1, sift_keypoints_1, sift_descriptors_1 );
    sift_extractor.compute( img_2, sift_keypoints_2, sift_descriptors_2 );

    //-- Step 3: Matching descriptor vectors using FLANN matcher
    FlannBasedMatcher matcher;
//    BFMatcher matcher(NORM_L2);

    std::vector< DMatch > surf_matches, sift_matches;
    matcher.match( surf_descriptors_1, surf_descriptors_2, surf_matches );
    matcher.match( sift_descriptors_1, sift_descriptors_2, sift_matches );

    double surf_max_dist = 0, surf_min_dist = 100, surf_avg_dist = 0;
    double sift_max_dist = 0, sift_min_dist = 100, sift_avg_dist = 0;

    //-- Quick calculation of max and min distances between keypoints
    for (int i = 0; i < surf_descriptors_1.rows; i++ ) { 
        double dist = surf_matches[i].distance;
        if( dist < surf_min_dist ) surf_min_dist = dist;
        if( dist > surf_max_dist ) surf_max_dist = dist;
        surf_avg_dist += dist;
    }
    surf_avg_dist /= surf_descriptors_1.rows;

    printf("-- surf avg dist : %f \n", surf_avg_dist );
    printf("-- surf max dist : %f \n", surf_max_dist );
    printf("-- surf min dist : %f \n", surf_min_dist );

    //-- Quick calculation of max and min distances between keypoints
    for (int i = 0; i < sift_descriptors_1.rows; i++ ) { 
        double dist = sift_matches[i].distance;
        if( dist < sift_min_dist ) sift_min_dist = dist;
        if( dist > sift_max_dist ) sift_max_dist = dist;
        sift_avg_dist += dist;
    }
    sift_avg_dist /= sift_descriptors_1.rows;

    printf("-- sift avg dist : %f \n", sift_avg_dist );
    printf("-- sift max dist : %f \n", sift_max_dist );
    printf("-- sift min dist : %f \n", sift_min_dist );


    //-- Draw only "good" matches (i.e. whose distance is less than 2*min_dist )
    //-- PS.- radiusMatch can also be used here.
    std::vector< DMatch > surf_good_matches, sift_good_matches;

    for (int i = 0; i < surf_descriptors_1.rows; i++ ) {
        if (surf_matches[i].distance <= 1.8 * surf_min_dist ) { 
            surf_good_matches.push_back( surf_matches[i]);
        }
    }

    for (int i = 0; i < sift_descriptors_1.rows; i++ ) {
        if (sift_matches[i].distance <= 1.8 * sift_min_dist ) { 
            sift_good_matches.push_back( sift_matches[i]);
        }
    }


    //-- Draw only "good" matches
    Mat surf_img_matches;
    drawMatches( img_1, surf_keypoints_1, img_2, surf_keypoints_2,
            surf_good_matches, surf_img_matches, Scalar::all(-1), Scalar::all(-1),
            std::vector<char>(), DrawMatchesFlags::NOT_DRAW_SINGLE_POINTS );

    Mat sift_img_matches;
    drawMatches( img_1, sift_keypoints_1, img_2, sift_keypoints_2,
            sift_good_matches, sift_img_matches, Scalar::all(-1), Scalar::all(-1),
            std::vector<char>(), DrawMatchesFlags::NOT_DRAW_SINGLE_POINTS );


    //-- Show detected matches
    namedWindow( "SURF Good Matches", CV_WINDOW_AUTOSIZE );
    imshow( "SURF Good Matches", surf_img_matches );

    //-- Show detected matches
    namedWindow( "SIFT Good Matches", CV_WINDOW_AUTOSIZE );
    imshow( "SIFT Good Matches", sift_img_matches );

//    resizeWindow( "SURF Good Matches", 1000, 1000);
//    resizeWindow( "SIFT Good Matches", 1000, 1000);

    /*
    for( int i = 0; i < good_matches.size(); i++ ) {
        printf( "-- Good Match [%d] Keypoint 1: %d  -- Keypoint 2: %d  \n", i, good_matches[i].queryIdx, good_matches[i].trainIdx ); }
    */

    waitKey(0);

    return 0;
}

