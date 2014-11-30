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

using std::ofstream;
using namespace cv;

void usage(int argc, char** argv) {
    std::cout << "Usage:" << std::endl;
    std::cout << "    " << argv[0] << " <count> <img1 ... imgN>" << std::endl;
}

int histogram_rows = 100;
int histogram_cols = 200;

void init_histograms(int ****histograms, int count, int histogram_cols) {
    std::cout << "initing histogram with count " << count << " and cols " << histogram_cols << std::endl;
    (*histograms) = new int**[count];
    for (int i = 0; i < count; i++) {
        (*histograms)[i] = new int*[3];
        (*histograms)[i][0] = new int[histogram_cols];
        (*histograms)[i][1] = new int[histogram_cols];
        (*histograms)[i][2] = new int[histogram_cols];
        for (int j = 0; j < histogram_cols; j++) {
            (*histograms)[i][0][j] = 0;
            (*histograms)[i][1][j] = 0;
            (*histograms)[i][2][j] = 0;
        }
    }
}

void delete_histograms(int ****histograms, int count) {
    for (int i = 0; i < count; i++) {
        delete [] (*histograms)[i][0];
        delete [] (*histograms)[i][1];
        delete [] (*histograms)[i][2];
    }
    delete [] (*histograms);
}


void print_histogram(const char* image_name, Mat &img, Mat &mod_img, int x1, int y1, int x2, int y2, int current, int ***histograms) {
//    std::cout << "printing histogram - x1: " << x1 << ", y1: " << y1 << ", x2: " << x2 << ", y2: " << y2 << std::endl;

    Mat histogram = Mat::zeros(histogram_rows, histogram_cols, CV_8UC3);


    float delta_x = x2 - x1;
    float delta_y = y2 - y1;
    float slope = delta_x / delta_y;
//    std::cout << "delta_x: " << delta_x << ", delta_y: " << delta_y << ", slope: " << slope << std::endl;

    for (int histogram_x = 0; histogram_x < histogram_cols; histogram_x++) {
        float distance = ((float)histogram_x / (float)histogram_cols);

        int img_x = (delta_x * distance) + x1;
        int img_y = (delta_y * distance) + y1;

        Vec3b pixel = img.at<Vec3b>(img_y, img_x);
        int b = histogram_rows * ((float)pixel.val[0] / 255.0);
        int g = histogram_rows * ((float)pixel.val[1] / 255.0);
        int r = histogram_rows * ((float)pixel.val[2] / 255.0);

        histogram.at<Vec3b>(b, histogram_x) = Vec3b(255, 0, 0);
        histogram.at<Vec3b>(g, histogram_x) = Vec3b(0, 255, 0);
        histogram.at<Vec3b>(r, histogram_x) = Vec3b(0, 0, 255);

        histograms[current][0][histogram_x] = b;
        histograms[current][1][histogram_x] = g;
        histograms[current][2][histogram_x] = r;

//        std::cout << "b_height: " << b << ", g_height: " << g << ", r_height: " << r << std::endl;

    }

    for (int histogram_x = 0; histogram_x < histogram_cols; histogram_x++) {
        float distance = ((float)histogram_x / (float)histogram_cols);

        int img_x = (delta_x * distance) + x1;
        int img_y = (delta_y * distance) + y1;

        mod_img.at<Vec3b>(img_y, img_x) = Vec3b(0, 0, 0);
//        std::cout << "histogram_x: " << histogram_x << ", x: " << img_x << ", y: " << img_y << std::endl;
    }

    std::ostringstream oss2;
    oss2 << image_name << " Histogram " << current;
    imshow(oss2.str().c_str(), histogram);

    moveWindow(oss2.str().c_str(), 100, 50 + ((histogram_rows + 50) * (current - 1)));

}

void print_radial_histograms(const char* image_name, int count, int ***histograms) {
    Mat img = imread( image_name, CV_LOAD_IMAGE_COLOR );
    Mat mod_img = img.clone();

    if ( !img.data ) {
        std::cout << "Error reading image '" << image_name << "'" << std::endl;
        exit(1);
    }

    int rows = img.rows;
    int cols = img.cols;
    std::cout << "img rows: " << rows << std::endl;
    std::cout << "img cols: " << cols << std::endl;

    float radian_min = 0, radian_max = 2 * M_PI, radian_step = radian_max / (float)count;

    int center_x = img.cols / 2.0;
    int center_y = img.rows / 2.0;
    int radius = sqrt( (img.cols * img.cols) + (img.rows * img.rows) );

    std::cout << "center_x: " << center_x << std::endl;
    std::cout << "center_y: " << center_y << std::endl;

    bool doing_width = true;
    int x1, y1, x2, y2;
    float degree_r = 0;
    for (int i = 0; i < count; i++) {
        int center_h = img.rows / 2.0;
        int center_w = img.cols / 2.0;

        int h = center_w * tan(degree_r); 
        if (center_h + h >= img.rows || center_h + h < 0) {
            if (degree_r > 0 && degree_r < M_PI) {
                y2 = center_h + center_h;
            } else {
                y2 = 0;
            }
            x2 = center_w + (center_h / tan(degree_r));
        } else {
            if (degree_r > M_PI / 2.0 && degree_r < 3.0 * M_PI / 2.0) {
                x2 = center_w + center_w;
            } else {
                x2 = 0;
            }
            y2 = center_h + h;
        }

        x1 = center_w;
        y1 = center_h;

        using std::setw;
        std::cout << "degree: " << setw(10) << degree_r << ", x1: " << setw(5) << x1 << ", y1: " << setw(5) << y1 << ", x2: " << setw(5) << x2 << ", y2: " << setw(5) << y2 << std::endl;

        print_histogram(image_name, img, mod_img, x1, y1, x2, y2, i, histograms);

        degree_r += radian_step;
    }

    imshow(image_name, mod_img);
    moveWindow(image_name, (histogram_cols + 200), 50);
}

/** @function main */
int main( int argc, char** argv ) {
    if (argc < 3) {
        usage(argc, argv);
        return -1;
    }

    int count = atoi(argv[1]);

    for (int i = 0; i < argc; i++) {
        std::cout << "    " << argv[i] << std::endl;
    }

    int ***histograms_1;
    init_histograms(&histograms_1, count, histogram_cols);
    print_radial_histograms(argv[2], count, histograms_1);

    int ***histograms_2;
    init_histograms(&histograms_2, count, histogram_cols);
    print_radial_histograms(argv[3], count, histograms_2);

    long b_dist, g_dist, r_dist;
    long min_b_dist = 999999999, min_g_dist = 999999999, min_r_dist = 999999999;
    long min_total = 999999999;

    int min_compare_1 = -1, min_compare_2 = -1;

    for (int j = 0; j < count; j++) {
        long sum_b = 0, sum_g = 0, sum_r = 0;

        int second = j;
        std::cout << "FIRST start " << 0 << " TO SECOND start " << second << std::endl;

        for (int i = 0; i < count; i++) {
            b_dist = dtw_distance(histograms_1[i][0], histogram_cols, histograms_2[second][0], histogram_cols, 10);
            g_dist = dtw_distance(histograms_1[i][1], histogram_cols, histograms_2[second][1], histogram_cols, 10);
            r_dist = dtw_distance(histograms_1[i][2], histogram_cols, histograms_2[second][2], histogram_cols, 10);

            sum_b += b_dist;
            sum_g += g_dist;
            sum_r += r_dist;

            std::cout << "dtw_distance " << i << " -- " << second << " (b) = " << b_dist << std::endl;
            std::cout << "dtw_distance " << i << " -- " << second << " (g) = " << g_dist << std::endl;
            std::cout << "dtw_distance " << i << " -- " << second << " (r) = " << r_dist << std::endl;
            std::cout << std::endl;
            second++;
            if (second >= count) second = 0;
        }
        std::cout << "    sum_b: " << sum_b << std::endl;
        std::cout << "    sum_g: " << sum_g << std::endl;
        std::cout << "    sum_r: " << sum_r << std::endl;
        std::cout << "    total: " << (sum_b + sum_g + sum_r) << std::endl;
        std::cout << std::endl;

        if ((sum_b + sum_g + sum_r) < min_total) {
            min_total = sum_b + sum_g + sum_r;
            min_b_dist = sum_b;
            min_g_dist = sum_g;
            min_r_dist = sum_r;
            min_compare_1 = j;
            min_compare_2 = 0;
        }
    }

    std::cout << "min compare (" << min_total << ") was " << min_compare_1 << " to " << min_compare_2 << std::endl;
    std::cout << "  min_b_dist: " << min_b_dist << std::endl;
    std::cout << "  min_g_dist: " << min_g_dist << std::endl;
    std::cout << "  min_r_dist: " << min_r_dist << std::endl;


    delete_histograms(&histograms_1, count);
    delete_histograms(&histograms_2, count);

    waitKey(0);

    return 0;
}

