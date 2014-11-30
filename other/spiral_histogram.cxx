#include <stdio.h>
#include <iostream>
#include <iomanip>
#include <string>
#include <sstream>
#include <fstream>
#include "opencv2/core/core.hpp"
#include "opencv2/opencv.hpp"
#include "opencv2/features2d/features2d.hpp"
#include "opencv2/nonfree/features2d.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/legacy/legacy.hpp"

#include "dynamic_time_warping.hxx"

using std::cin;
using std::cout;
using std::endl;
using std::ofstream;
using std::ostringstream;
using std::setw;
using namespace cv;

int histogram_rows = 255;

void init_histograms(int ***histograms, int samples) {
    cout << "initing histogram with " << samples << " cols and " << histogram_rows << " rows." << endl;
    (*histograms) = new int*[3];
    (*histograms)[0] = new int[samples];
    (*histograms)[1] = new int[samples];
    (*histograms)[2] = new int[samples];
    for (int i = 0; i < samples; i++) {
        (*histograms)[0][i] = 0;
        (*histograms)[1][i] = 0;
        (*histograms)[2][i] = 0;
    }
}

void delete_histograms(int ***histograms, int samples) {
    delete [] (*histograms)[0];
    delete [] (*histograms)[1];
    delete [] (*histograms)[2];
    delete [] (*histograms);
}

/**
 *  length of histogram_1 and histogram_2 == samples
 */
void compare_spirals(int samples, double step_size_radians, Mat &img_1, double a1, double b1, int **histogram_1, Mat &mod_img_1, Mat &img_2, double a2, double b2, int **histogram_2, Mat &mod_img_2) {
    //r = a + b*theta
    //  a turns the spiral
    //  b makes it expand
    //x = r * cos( theta )
    //y = r * sin( theta )

    int b, g, r;
    Vec3b pixel;

    double r1, r2, theta = 0;
    double x1, x2, y1, y2;

    int x_center_1 = img_1.cols / 2.0;
    int y_center_1 = img_1.rows / 2.0;

    int x_center_2 = img_2.cols / 2.0;
    int y_center_2 = img_2.rows / 2.0;

    for (int i = 0; i < samples; i++) {
        r1 = (b1 * theta);     //archimedes spiral equation
        r2 = (b2 * theta);

        x1 = x_center_1 + (r1 * cos(theta + a1));
        y1 = y_center_1 + (r1 * sin(theta + a1));

        x2 = x_center_2 + (r2 * cos(theta + a2));
        y2 = y_center_2 + (r2 * sin(theta + a2));

//        cout << "  x1: " << setw(4) << x1 
//             << ", y1: " << setw(4) << y1
//             << ", x2: " << setw(4) << y1
//             << ", y2: " << setw(4) << y1 << endl;

        pixel = img_1.at<Vec3b>(y1, x1);
        b = histogram_rows * ((float)pixel.val[0] / 255.0);
        g = histogram_rows * ((float)pixel.val[1] / 255.0);
        r = histogram_rows * ((float)pixel.val[2] / 255.0);
        histogram_1[0][i] = b;
        histogram_1[1][i] = g;
        histogram_1[2][i] = r;

        pixel = img_2.at<Vec3b>(y2, x2);
        b = histogram_rows * ((float)pixel.val[0] / 255.0);
        g = histogram_rows * ((float)pixel.val[1] / 255.0);
        r = histogram_rows * ((float)pixel.val[2] / 255.0);
        histogram_2[0][i] = b;
        histogram_2[1][i] = g;
        histogram_2[2][i] = r;

        mod_img_1.at<Vec3b>(y1, x1) = Vec3b(0, 0, 0);
        mod_img_2.at<Vec3b>(y2, x2) = Vec3b(0, 0, 0);

        theta += step_size_radians;
    }
}

void usage(int argc, char** argv) {
    cout << "Usage:" << endl;
    cout << "    " << argv[0] << " <img1> <img2> <samples> <step_size_radians> <a1> <b1>" << endl;
}


/** @function main */
int main( int argc, char** argv ) {
    if (argc < 7) {
        usage(argc, argv);
        return -1;
    }

    for (int i = 0; i < argc; i++) {
        cout << "    " << argv[i] << endl;
    }

    int samples = atoi(argv[1]);
    double step_size_radians = atof(argv[2]);

    double a1 = atof(argv[3]);
    double a2 = a1;
    double b1 = atof(argv[4]);
    double b2 = b1;

    int **histograms_1;
    int **histograms_2;
    init_histograms(&histograms_1, samples);
    init_histograms(&histograms_2, samples);

    int x_pos = 100;
    int y_pos = 100;
    int current = 0;
    for (int i = 5; i < argc; i++) {
        for (int j = 5; j < argc; j++) {
            if (i == j) continue;

            cout << setw(40) << argv[i] << setw(40) << argv[j];

            Mat img_1 = imread( argv[i], CV_LOAD_IMAGE_COLOR );
            Mat img_2 = imread( argv[j], CV_LOAD_IMAGE_COLOR );

            for (int k = 0; k < 80; k++) {
                Mat mod_img_1 = img_1.clone();
                Mat mod_img_2 = img_2.clone();

                compare_spirals(samples, step_size_radians, img_1, a1, b1, histograms_1, mod_img_1, img_2, a2 + (2 * M_PI * (k / 80.0)), b2, histograms_2, mod_img_2);

                ostringstream name1;
                name1 << "i1_" << current;
                ostringstream name2;
                name2 << "i2_" << current;

//                imshow(name1.str().c_str(), mod_img_1);
                imshow(name2.str().c_str(), mod_img_2);

//                moveWindow(name1.str().c_str(), 100, 200 * current);
                moveWindow(name2.str().c_str(), x_pos, y_pos);

                y_pos += 200;
                if (y_pos > 1000) {
                    y_pos = 100; 
                    x_pos += 200;
                }

                double sum_distance = dtw_distance(histograms_1[0], samples, histograms_2[0], samples, 10) +
                                      dtw_distance(histograms_1[1], samples, histograms_2[1], samples, 10) +
                                      dtw_distance(histograms_1[2], samples, histograms_2[2], samples, 10);

                cout << setw(10) << sum_distance << endl;
                current++;
            }

            cout << endl;
        }
        cout << endl;
    }

    delete_histograms(&histograms_1, samples);
    delete_histograms(&histograms_2, samples);

    waitKey(0);

    return 0;
}

