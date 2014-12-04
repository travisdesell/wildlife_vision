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

//from UNDVC_COMMON
#include "vector_io.hxx"
#include "arguments.hxx"



//from TAO
#include "neural_networks/convolutional_neural_network.hxx"

using namespace std;
using namespace cv;

int main(int argc, char** argv) {
    vector<string> arguments = vector<string>(argv, argv + argc);


    int rowscols;
    get_argument(arguments, "--rowscols", true, rowscols);

    int img_reduction = 128 / rowscols;

    string conv_net_file, input_image;
    get_argument(arguments, "--conv_net", true, conv_net_file);
    get_argument(arguments, "--image", true, input_image);

    cout << "opening conv net file: " << conv_net_file << endl;
    ifstream infile(conv_net_file.c_str());

    string line;
    getline(infile, line);
    getline(infile, line);

    vector<double> weights;
    string_to_vector(line, weights);

    cout << "weights vector size: " << weights.size() << endl;

    infile.close();

    cout << "opening image: " << input_image << endl;
    Mat src = imread( input_image.c_str(), CV_LOAD_IMAGE_COLOR);

    cout << "source image size:       " << src.cols << ", rows: " << src.rows << endl;

    Size size(src.cols / img_reduction, src.rows / img_reduction); /*width, height*/

    Mat resized_image;
    resize(src, resized_image, size);

    imshow("resized image", resized_image);
    imwrite("resized_image.png", resized_image);

    vector<int> conv_sizes;
    vector<int> max_pool_sizes;
    get_argument_vector(arguments, "--convolutional_sizes", true, conv_sizes);
    get_argument_vector(arguments, "--max_pool_sizes", true, max_pool_sizes);

    if (conv_sizes.size() != max_pool_sizes.size()) {
        cerr << "ERROR: convolutional_sizes.size() [" << conv_sizes.size() << "] != max_pool_sizes.size() [" << max_pool_sizes.size() << "]" << endl;
        exit(1);
    }
    vector< pair<int,int> > layers;
    for (int i = 0; i < conv_sizes.size(); i++) {
        layers.push_back(pair<int, int>(conv_sizes[i], max_pool_sizes[i]));
    }

    int fc_size;
    get_argument(arguments, "--fully_connected_size", true, fc_size);

    vector< vector< vector<char> > > images(2);    //can ignore this

    bool quiet = false;
    ConvolutionalNeuralNetwork *conv_nn = new ConvolutionalNeuralNetwork(rowscols, rowscols, true, quiet, images, layers, fc_size);
    conv_nn->set_weights(weights);

    Mat classified_image = Mat::zeros( resized_image.rows - rowscols, resized_image.cols - rowscols, CV_8UC3 );

    for (int i = 0; i < resized_image.rows - rowscols; i++) {
        for (int j = 0; j < resized_image.cols - rowscols; j++) {
            vector<char> current_image;

            for (int k = 0; k < rowscols; k++) {
                for (int l = 0; l < rowscols; l++) {
                    Vec3b pixel = resized_image.at<Vec3b>(i + k, j + l);
                    current_image.push_back(pixel[0]);
                    current_image.push_back(pixel[1]);
                    current_image.push_back(pixel[2]);
                }
            }

            conv_nn->evaluate(current_image, 0);
            short r = (short)(conv_nn->get_output_class(0) * 255.0);
            short g = 0;
            short b = (short)(conv_nn->get_output_class(1) * 255.0);
            classified_image.at<Vec3b>(i, j) = Vec3b(r, g, b);
        }
        cout << i << " / " << (resized_image.rows - rowscols) << endl;
    }

    imshow("classified image", classified_image);
    imwrite("classified_image.png", classified_image);

    waitKey(0);

    return 0;
}

